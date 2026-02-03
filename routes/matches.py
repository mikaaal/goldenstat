import re
import sqlite3
from datetime import datetime
from flask import Blueprint, request, jsonify, render_template

matches_bp = Blueprint('matches', __name__)


def _get_current_db_path():
    from app import get_current_db_path
    return get_current_db_path()


def _parse_match_position(match_name, match_type):
    from app import parse_match_position
    return parse_match_position(match_name, match_type)


@matches_bp.route('/api/sub_match/<int:sub_match_id>')
def get_sub_match_info(sub_match_id):
    """Get basic sub-match information with corrected player names"""
    try:
        with sqlite3.connect(_get_current_db_path()) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # Get sub-match info with teams and players
            cursor.execute("""
                SELECT
                    sm.*,
                    m.match_date,
                    t1.name as team1_name,
                    t2.name as team2_name
                FROM sub_matches sm
                JOIN matches m ON sm.match_id = m.id
                JOIN teams t1 ON m.team1_id = t1.id
                JOIN teams t2 ON m.team2_id = t2.id
                WHERE sm.id = ?
            """, (sub_match_id,))

            sub_match = cursor.fetchone()
            if not sub_match:
                return jsonify({'error': 'Sub-match not found'}), 404

            # Get players for each team
            team_players = {}

            for team_num in [1, 2]:
                cursor.execute("""
                    SELECT
                        p.name as original_name,
                        smp.player_avg,
                        smp.player_id
                    FROM sub_match_participants smp
                    JOIN players p ON smp.player_id = p.id
                    WHERE smp.sub_match_id = ? AND smp.team_number = ?
                    ORDER BY p.name
                """, (sub_match_id, team_num))

                players = cursor.fetchall()
                canonical_players = []

                for player in players:
                    # Check if this player is mapped to a different name for this sub-match
                    cursor.execute("""
                        SELECT correct_player_name
                        FROM sub_match_player_mappings
                        WHERE sub_match_id = ? AND original_player_id = ?
                    """, (sub_match_id, player['player_id']))

                    mapping_result = cursor.fetchone()

                    if mapping_result:
                        # Use the mapped name
                        display_name = mapping_result['correct_player_name']
                        print(f"DEBUG: Mapped {player['original_name']} -> {display_name} for sub-match {sub_match_id}")
                    else:
                        # Use the original name
                        display_name = player['original_name']

                    canonical_players.append({
                        'name': display_name,
                        'player_id': player['player_id'],
                        'average': player['player_avg']
                    })

                # Deduplicate: if "Erik" and "Erik (Oilers)" both appear with the same avg,
                # keep only the disambiguated version
                deduplicated = []
                for p in canonical_players:
                    dominated = False
                    for other in canonical_players:
                        if other is p:
                            continue
                        # Check if other's name is a disambiguated version of p's name
                        if (other['name'].startswith(p['name'] + ' (') and
                                other['name'].endswith(')') and
                                other['average'] == p['average']):
                            dominated = True
                            break
                    if not dominated:
                        deduplicated.append(p)

                team_players[f'team{team_num}_players'] = deduplicated

            return jsonify({
                'sub_match_info': dict(sub_match),
                **team_players
            })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@matches_bp.route('/api/sub_match/<int:sub_match_id>/throws/<player_name>')
def get_sub_match_player_throws(sub_match_id, player_name):
    """Get detailed throw data for a specific player in a specific sub-match"""
    try:
        from urllib.parse import unquote
        player_name = unquote(player_name)

        # Handle team disambiguation like "Robban (Balsta)" -> "Robban"
        with sqlite3.connect(_get_current_db_path()) as temp_conn:
            temp_cursor = temp_conn.cursor()
            temp_cursor.execute("SELECT id FROM players WHERE name = ?", (player_name,))
            is_exact_match = temp_cursor.fetchone() is not None

        if '(' in player_name and player_name.endswith(')') and not is_exact_match:
            player_name = player_name.split(' (')[0]

        with sqlite3.connect(_get_current_db_path()) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # Handle both direct players and mapped players
            final_canonical_name = player_name

            # First try direct participant lookup by name
            cursor.execute("""
                SELECT p.id as player_id, p.name
                FROM players p
                JOIN sub_match_participants smp ON p.id = smp.player_id
                WHERE p.name = ? AND smp.sub_match_id = ?
            """, (final_canonical_name, sub_match_id))

            player_result = cursor.fetchone()

            if player_result:
                actual_player_id = player_result['player_id']
            else:
                # Check if this is a mapped player for this specific sub-match
                cursor.execute("""
                    SELECT smpm.original_player_id
                    FROM sub_match_player_mappings smpm
                    WHERE smpm.sub_match_id = ? AND smpm.correct_player_name = ?
                """, (sub_match_id, player_name))

                mapping_result = cursor.fetchone()

                if mapping_result:
                    actual_player_id = mapping_result['original_player_id']
                else:
                    # Fallback: just look up by name
                    cursor.execute("SELECT id as player_id, name FROM players WHERE name = ?", (final_canonical_name,))
                    player_result = cursor.fetchone()
                    if not player_result:
                        return jsonify({'error': 'Player not found'}), 404
                    actual_player_id = player_result['player_id']

            # Get sub-match info using the actual player who participated
            cursor.execute("""
                SELECT
                    sm.*,
                    smp.team_number,
                    smp.player_avg,
                    smp.player_id,
                    m.match_date,
                    t1.name as team1_name,
                    t2.name as team2_name
                FROM sub_matches sm
                JOIN sub_match_participants smp ON sm.id = smp.sub_match_id
                JOIN players p ON smp.player_id = p.id
                JOIN matches m ON sm.match_id = m.id
                JOIN teams t1 ON m.team1_id = t1.id
                JOIN teams t2 ON m.team2_id = t2.id
                WHERE sm.id = ? AND smp.player_id = ?
            """, (sub_match_id, actual_player_id))

            sub_match_info = cursor.fetchone()
            if not sub_match_info:
                return jsonify({'error': 'Player did not participate in this sub-match'}), 404

            player_id = sub_match_info['player_id']

            # Get opponent info and averages with correct mapped names
            opposing_team_number = 2 if sub_match_info['team_number'] == 1 else 1
            cursor.execute("""
                SELECT p.name as original_name, smp.player_avg, smp.player_id
                FROM sub_match_participants smp
                JOIN players p ON smp.player_id = p.id
                WHERE smp.sub_match_id = ? AND smp.team_number = ?
                ORDER BY p.name
            """, (sub_match_id, opposing_team_number))

            opponent_data = cursor.fetchall()
            opponents = []
            opponent_avgs = []

            for opponent in opponent_data:
                # Check for mapping
                cursor.execute("""
                    SELECT correct_player_name
                    FROM sub_match_player_mappings
                    WHERE sub_match_id = ? AND original_player_id = ?
                """, (sub_match_id, opponent['player_id']))

                mapping_result = cursor.fetchone()
                display_name = mapping_result['correct_player_name'] if mapping_result else opponent['original_name']

                opponents.append(display_name)
                opponent_avgs.append(opponent['player_avg'] or 0)

            opponent_names = ' / '.join(opponents) if len(opponents) > 1 else (opponents[0] if opponents else 'Okand')
            opponent_avg = sum(opponent_avgs) / len(opponent_avgs) if opponent_avgs else 0

            # Get teammate info (other players on the same team) with correct mapped names
            cursor.execute("""
                SELECT p.name as original_name, smp.player_avg, smp.player_id
                FROM sub_match_participants smp
                JOIN players p ON smp.player_id = p.id
                WHERE smp.sub_match_id = ? AND smp.team_number = ? AND smp.player_id != ?
                ORDER BY p.name
            """, (sub_match_id, sub_match_info['team_number'], player_id))

            teammate_data = cursor.fetchall()
            teammates = []

            for teammate in teammate_data:
                # Check for mapping
                cursor.execute("""
                    SELECT correct_player_name
                    FROM sub_match_player_mappings
                    WHERE sub_match_id = ? AND original_player_id = ?
                """, (sub_match_id, teammate['player_id']))

                mapping_result = cursor.fetchone()
                display_name = mapping_result['correct_player_name'] if mapping_result else teammate['original_name']
                teammates.append(display_name)

            teammate_names = ' / '.join(teammates) if teammates else None

            # Get all throws for both players in this sub-match
            # Filter out starting throw (score=0, remaining_score=501)
            # Use DISTINCT to eliminate duplicates that may exist in the database
            cursor.execute("""
                SELECT DISTINCT
                    t.score,
                    t.remaining_score,
                    t.darts_used,
                    t.round_number,
                    t.team_number,
                    l.leg_number,
                    l.winner_team,
                    l.total_rounds as leg_total_rounds
                FROM throws t
                JOIN legs l ON t.leg_id = l.id
                WHERE l.sub_match_id = ?
                  AND NOT (t.score = 0 AND t.remaining_score = 501)
                ORDER BY l.leg_number, t.round_number, t.team_number
            """, (sub_match_id,))

            throws = [dict(row) for row in cursor.fetchall()]

            # Separate throws by player and opponent
            player_throws = [t for t in throws if t['team_number'] == sub_match_info['team_number']]
            opponent_throws = [t for t in throws if t['team_number'] != sub_match_info['team_number']]

            # Group throws by leg with both player and opponent data
            legs_with_throws = {}

            for throw in throws:
                leg_num = throw['leg_number']
                if leg_num not in legs_with_throws:
                    # Determine leg winner by looking for negative throws
                    cursor.execute("""
                        SELECT team_number FROM throws t
                        JOIN legs l ON t.leg_id = l.id
                        WHERE l.sub_match_id = ? AND l.leg_number = ? AND t.score < 0
                        LIMIT 1
                    """, (sub_match_id, leg_num))
                    winning_throw_result = cursor.fetchone()

                    if winning_throw_result:
                        leg_winner_team = winning_throw_result[0]
                    else:
                        # Fallback to stored winner_team if available
                        leg_winner_team = throw['winner_team']

                    legs_with_throws[leg_num] = {
                        'leg_number': leg_num,
                        'winner_team': leg_winner_team,
                        'leg_total_rounds': throw['leg_total_rounds'],
                        'player_won_leg': leg_winner_team == sub_match_info['team_number'],
                        'player_throws': [],
                        'opponent_throws': []
                    }

            # Add throws to appropriate player/opponent lists
            for throw in player_throws:
                leg_num = throw['leg_number']
                legs_with_throws[leg_num]['player_throws'].append({
                    'round_number': throw['round_number'],
                    'score': throw['score'],
                    'remaining_score': throw['remaining_score'],
                    'darts_used': throw['darts_used']
                })

            for throw in opponent_throws:
                leg_num = throw['leg_number']
                legs_with_throws[leg_num]['opponent_throws'].append({
                    'round_number': throw['round_number'],
                    'score': throw['score'],
                    'remaining_score': throw['remaining_score'],
                    'darts_used': throw['darts_used']
                })

            # Calculate statistics for both players
            def calculate_player_stats(throws_list, team_number):
                total_throws = len(throws_list)
                scores = [t['score'] for t in throws_list if t['score'] >= 0]
                total_score = sum(scores)

                # Calculate total darts used for proper average calculation
                total_darts = 0
                for throw in throws_list:
                    if throw['score'] < 0:
                        # Checkout throw - use the dart count
                        total_darts += abs(throw['score'])
                    else:
                        # Regular throw - use 3 darts (or darts_used if available)
                        total_darts += throw.get('darts_used', 3)

                # Use the database player_avg instead of calculating it
                avg_score = sub_match_info['player_avg'] if team_number == sub_match_info['team_number'] else opponent_avg
                max_score = max(scores, default=0)
                legs_won = sum(1 for leg in legs_with_throws.values() if leg['winner_team'] == team_number)

                # Get checkout scores (what they actually scored to finish)
                checkout_scores = []
                for throw in throws_list:
                    if throw['score'] < 0:
                        # Find what score was needed to finish (remaining_score before the checkout)
                        cursor.execute("""
                            SELECT remaining_score
                            FROM throws
                            WHERE leg_id = (SELECT id FROM legs WHERE sub_match_id = ? AND leg_number = ?)
                              AND team_number = ? AND round_number = ?
                        """, (sub_match_id, throw['leg_number'], team_number, throw['round_number'] - 1))

                        checkout_result = cursor.fetchone()
                        if checkout_result:
                            checkout_score = checkout_result[0]  # This is what they scored to finish
                            checkout_scores.append(checkout_score)

                # Advanced statistics
                all_scores = scores + checkout_scores
                throws_100_139 = len([s for s in all_scores if 100 <= s < 140])
                throws_140_179 = len([s for s in all_scores if 140 <= s < 180])
                throws_180 = len([s for s in all_scores if s == 180])
                throws_100_plus_total = len([s for s in all_scores if s >= 100])
                throws_under_20 = len([s for s in scores if s < 20])
                throws_60_plus = len([s for s in all_scores if s >= 60])

                # Calculate "Forsta 9 pil" (first 3 rounds average across all legs)
                first_9_dart_scores = []
                for leg in legs_with_throws.values():
                    leg_throws_key = 'player_throws' if team_number == sub_match_info['team_number'] else 'opponent_throws'
                    leg_throws = leg[leg_throws_key]
                    # Take first 3 throws (rounds) from each leg
                    for i, throw in enumerate(leg_throws):
                        if i < 3 and throw['score'] >= 0:  # Only first 3 rounds and only positive scores
                            first_9_dart_scores.append(throw['score'])

                first_9_dart_avg = round(sum(first_9_dart_scores) / max(1, len(first_9_dart_scores)), 2) if first_9_dart_scores else 0

                checkouts = [-t['score'] for t in throws_list if t['score'] < 0]
                total_checkouts = len(checkouts)
                checkout_darts = sum(checkouts) if checkouts else 0

                # Calculate special leg achievements (only for legs won by this player)
                short_legs = 0  # 18 darts or fewer (6 rounds or fewer)
                short_legs_detail = []  # List of actual dart counts for short legs
                high_finishes = 0  # 100+ checkout
                high_finishes_detail = []  # List of actual checkout scores

                for leg in legs_with_throws.values():
                    if leg['winner_team'] == team_number:
                        # Count throws for this player in this leg
                        leg_throws_key = 'player_throws' if team_number == sub_match_info['team_number'] else 'opponent_throws'
                        leg_throws = leg.get(leg_throws_key, [])

                        # Calculate total darts used in this leg
                        total_darts_in_leg = 0
                        checkout_score = 0

                        for throw in leg_throws:
                            # Use darts_used field if available, otherwise default to 3
                            total_darts_in_leg += throw.get('darts_used', 3)

                        # Check for short leg (18 darts or fewer)
                        if total_darts_in_leg <= 18:
                            short_legs += 1
                            short_legs_detail.append(total_darts_in_leg)

                        # Check for high finish (100+)
                        # Get actual checkout score from the previous throw (remaining_score before checkout)
                        cursor.execute("""
                            SELECT t_prev.remaining_score as checkout_score
                            FROM throws t_checkout
                            JOIN legs l ON t_checkout.leg_id = l.id
                            JOIN throws t_prev ON t_prev.leg_id = l.id
                              AND t_prev.team_number = t_checkout.team_number
                              AND t_prev.round_number = t_checkout.round_number - 1
                            WHERE l.sub_match_id = ? AND l.leg_number = ?
                              AND t_checkout.team_number = ? AND t_checkout.remaining_score = 0
                        """, (sub_match_id, leg['leg_number'], team_number))

                        checkout_result = cursor.fetchone()
                        if checkout_result and checkout_result[0] >= 100:
                            high_finishes += 1
                            high_finishes_detail.append(checkout_result[0])

                # Sort details for proper display order
                short_legs_detail.sort()  # Sort in ascending order
                high_finishes_detail.sort(reverse=True)  # Sort high finishes in descending order

                return {
                    'total_throws': total_throws,
                    'total_score': total_score,
                    'average_score': avg_score,
                    'max_score': max_score,
                    'legs_won': legs_won,
                    'throws_100_139': throws_100_139,
                    'throws_140_179': throws_140_179,
                    'throws_180': throws_180,
                    'throws_100_plus_total': throws_100_plus_total,
                    'throws_under_20': throws_under_20,
                    'throws_60_plus': throws_60_plus,
                    'total_checkouts': total_checkouts,
                    'checkout_darts': checkout_darts,
                    'short_legs': short_legs,
                    'short_legs_detail': short_legs_detail,
                    'high_finishes': high_finishes,
                    'high_finishes_detail': high_finishes_detail,
                    'first_9_dart_avg': first_9_dart_avg
                }

            player_stats = calculate_player_stats(player_throws, sub_match_info['team_number'])
            opponent_stats = calculate_player_stats(opponent_throws, opposing_team_number)

            # Determine correct team names based on which team the player is on
            if sub_match_info['team_number'] == 1:
                player_team_name = sub_match_info['team1_name']
                opponent_team_name = sub_match_info['team2_name']
            else:
                player_team_name = sub_match_info['team2_name']
                opponent_team_name = sub_match_info['team1_name']

            # Create corrected sub_match_info with proper team order
            corrected_sub_match_info = dict(sub_match_info)
            corrected_sub_match_info['team1_name'] = player_team_name
            corrected_sub_match_info['team2_name'] = opponent_team_name

            return jsonify({
                'sub_match_info': corrected_sub_match_info,
                'player_name': final_canonical_name,
                'opponent_names': opponent_names,
                'teammate_names': teammate_names,
                'legs': list(legs_with_throws.values()),
                'player_statistics': {
                    **player_stats,
                    'legs_total': len(legs_with_throws)
                },
                'opponent_statistics': {
                    **opponent_stats,
                    'legs_total': len(legs_with_throws)
                }
            })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@matches_bp.route('/api/sub_match/<int:sub_match_id>/match_id')
def get_sub_match_match_id(sub_match_id):
    """Get the parent match_id for a sub_match"""
    try:
        with sqlite3.connect(_get_current_db_path()) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute("""
                SELECT match_id FROM sub_matches WHERE id = ?
            """, (sub_match_id,))

            result = cursor.fetchone()
            if not result:
                return jsonify({'error': 'Sub-match not found'}), 404

            return jsonify({'match_id': result['match_id']})

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@matches_bp.route('/api/match/<int:match_id>/legs')
def get_match_legs(match_id):
    """Get detailed leg information for a match"""
    try:
        with sqlite3.connect(_get_current_db_path()) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # Get match info
            cursor.execute("""
                SELECT m.*, t1.name as team1_name, t2.name as team2_name
                FROM matches m
                JOIN teams t1 ON m.team1_id = t1.id
                JOIN teams t2 ON m.team2_id = t2.id
                WHERE m.id = ?
            """, (match_id,))

            match_info = cursor.fetchone()
            if not match_info:
                return jsonify({'error': 'Match not found'}), 404

            # Get all sub-matches with legs
            cursor.execute("""
                SELECT
                    sm.*,
                    l.id as leg_id,
                    l.leg_number,
                    l.winner_team,
                    l.first_player_team,
                    l.total_rounds
                FROM sub_matches sm
                LEFT JOIN legs l ON sm.id = l.sub_match_id
                WHERE sm.match_id = ?
                ORDER BY sm.match_number, l.leg_number
            """, (match_id,))

            legs_data = cursor.fetchall()

            # Group by sub-match
            sub_matches = {}
            for row in legs_data:
                sm_id = row['id']
                if sm_id not in sub_matches:
                    sub_matches[sm_id] = {
                        'sub_match_id': sm_id,
                        'match_type': row['match_type'],
                        'match_name': row['match_name'],
                        'team1_legs': row['team1_legs'],
                        'team2_legs': row['team2_legs'],
                        'legs': []
                    }

                if row['leg_id']:  # Only add if leg exists
                    sub_matches[sm_id]['legs'].append({
                        'leg_number': row['leg_number'],
                        'winner_team': row['winner_team'],
                        'first_player_team': row['first_player_team'],
                        'total_rounds': row['total_rounds']
                    })

            return jsonify({
                'match_info': dict(match_info),
                'sub_matches': list(sub_matches.values())
            })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@matches_bp.route('/api/match/<int:match_id>/overview')
def get_match_overview(match_id):
    """Get overview of all sub-matches in a series match"""
    try:
        with sqlite3.connect(_get_current_db_path()) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # Get match info
            cursor.execute("""
                SELECT
                    m.id,
                    m.match_date,
                    m.season,
                    m.division,
                    t1.name as team1_name,
                    t2.name as team2_name,
                    m.team1_score,
                    m.team2_score
                FROM matches m
                JOIN teams t1 ON m.team1_id = t1.id
                JOIN teams t2 ON m.team2_id = t2.id
                WHERE m.id = ?
            """, (match_id,))

            match_info = cursor.fetchone()
            if not match_info:
                return jsonify({'error': 'Match not found'}), 404

            # Get all sub-matches for this match
            cursor.execute("""
                SELECT
                    sm.id,
                    sm.match_name,
                    sm.match_type,
                    sm.team1_legs,
                    sm.team2_legs
                FROM sub_matches sm
                WHERE sm.match_id = ?
                ORDER BY sm.id
            """, (match_id,))

            sub_matches_raw = cursor.fetchall()

            # Process each sub-match to get player info and averages
            sub_matches = []
            for sm in sub_matches_raw:
                # Parse position from match_name (e.g., "Team A vs Team B Doubles1" -> "D1")
                position = _parse_match_position(sm['match_name'], sm['match_type'])

                # Get players for team 1
                cursor.execute("""
                    SELECT
                        p.name as original_name,
                        smp.player_avg,
                        smp.player_id
                    FROM sub_match_participants smp
                    JOIN players p ON smp.player_id = p.id
                    WHERE smp.sub_match_id = ? AND smp.team_number = 1
                    ORDER BY p.name
                """, (sm['id'],))

                team1_players_raw = cursor.fetchall()
                team1_players = []
                team1_avg = 0

                for player in team1_players_raw:
                    # Check for player mapping
                    cursor.execute("""
                        SELECT correct_player_name
                        FROM sub_match_player_mappings
                        WHERE sub_match_id = ? AND original_player_id = ?
                    """, (sm['id'], player['player_id']))
                    mapping = cursor.fetchone()
                    name = mapping['correct_player_name'] if mapping else player['original_name']
                    team1_players.append(name)
                    if player['player_avg']:
                        team1_avg = max(team1_avg, player['player_avg'])

                # Get players for team 2
                cursor.execute("""
                    SELECT
                        p.name as original_name,
                        smp.player_avg,
                        smp.player_id
                    FROM sub_match_participants smp
                    JOIN players p ON smp.player_id = p.id
                    WHERE smp.sub_match_id = ? AND smp.team_number = 2
                    ORDER BY p.name
                """, (sm['id'],))

                team2_players_raw = cursor.fetchall()
                team2_players = []
                team2_avg = 0

                for player in team2_players_raw:
                    # Check for player mapping
                    cursor.execute("""
                        SELECT correct_player_name
                        FROM sub_match_player_mappings
                        WHERE sub_match_id = ? AND original_player_id = ?
                    """, (sm['id'], player['player_id']))
                    mapping = cursor.fetchone()
                    name = mapping['correct_player_name'] if mapping else player['original_name']
                    team2_players.append(name)
                    if player['player_avg']:
                        team2_avg = max(team2_avg, player['player_avg'])

                # Derive match_type from position (handles imports where Dubbel was tagged as Singles)
                effective_match_type = 'Doubles' if position.startswith('D') or position == 'AD' else 'Singles'

                sub_matches.append({
                    'id': sm['id'],
                    'position': position,
                    'match_type': effective_match_type,
                    'team1_players': ' / '.join(team1_players),
                    'team2_players': ' / '.join(team2_players),
                    'team1_legs': sm['team1_legs'],
                    'team2_legs': sm['team2_legs'],
                    'team1_avg': round(team1_avg, 2) if team1_avg else None,
                    'team2_avg': round(team2_avg, 2) if team2_avg else None
                })

            # Sort sub_matches by position order (differs between leagues)
            league = request.args.get('league', '')
            if league == 'riksserien':
                if len(sub_matches) <= 10:
                    # Elit Dam format: S1-S4, D1, S5-S8, D2
                    position_order = {
                        'S1': 1, 'S2': 2, 'S3': 3, 'S4': 4,
                        'D1': 5,
                        'S5': 6, 'S6': 7, 'S7': 8, 'S8': 9,
                        'D2': 10,
                        'AD': 100
                    }
                else:
                    # Standard Riksserien: S1-S8, D1, S9-S16, D2
                    position_order = {
                        'S1': 1, 'S2': 2, 'S3': 3, 'S4': 4, 'S5': 5, 'S6': 6, 'S7': 7, 'S8': 8,
                        'D1': 9,
                        'S9': 10, 'S10': 11, 'S11': 12, 'S12': 13, 'S13': 14, 'S14': 15, 'S15': 16, 'S16': 17,
                        'D2': 18,
                        'AD': 100
                    }
            else:
                # Stockholmsserien: D1, S1, S2, D2, S3, S4, D3, S5, S6, AD
                position_order = {
                    'D1': 1, 'S1': 2, 'S2': 3, 'D2': 4, 'S3': 5, 'S4': 6,
                    'D3': 7, 'S5': 8, 'S6': 9,
                    'AD': 100
                }
            sub_matches.sort(key=lambda x: position_order.get(x['position'], 50))

            # Calculate sub-match wins for each team
            # In Riksserien, doubles wins are worth 2 points
            team1_sub_wins = 0
            team2_sub_wins = 0
            for sm in sub_matches:
                points = 2 if (league == 'riksserien' and sm['match_type'] == 'Doubles') else 1
                if sm['team1_legs'] > sm['team2_legs']:
                    team1_sub_wins += points
                elif sm['team2_legs'] > sm['team1_legs']:
                    team2_sub_wins += points

            return jsonify({
                'match_info': dict(match_info),
                'sub_matches': sub_matches,
                'team1_sub_wins': team1_sub_wins,
                'team2_sub_wins': team2_sub_wins
            })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@matches_bp.route('/match_overview')
def match_overview():
    """Page to show all sub-matches in a series match"""
    league = request.args.get('league', '')
    return render_template('match_overview.html', league=league)


@matches_bp.route('/sub_match_throws')
def sub_match_throws():
    """Sub-match throws visualization page"""
    league = request.args.get('league', '')
    return render_template('sub_match_throws.html', league=league)


@matches_bp.route('/test_throws')
def test_throws():
    """Test page for throws visualization"""
    league = request.args.get('league', '')
    return render_template('test_throws.html', league=league)


@matches_bp.route('/series_matches')
def series_matches():
    """Page to show all series matches grouped by week"""
    league = request.args.get('league', '')
    return render_template('series_matches.html', league=league)


@matches_bp.route('/api/series_matches')
def get_series_matches():
    """Get all series matches grouped by week"""
    try:
        # Get filter parameters
        season = request.args.get('season')
        division = request.args.get('division')

        with sqlite3.connect(_get_current_db_path()) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # Build query with optional filters
            where_clauses = []
            params = []

            if season:
                where_clauses.append("m.season = ?")
                params.append(season)
            if division:
                where_clauses.append("m.division = ?")
                params.append(division)

            where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""

            # Get all matches with sub-match win counts
            # In Riksserien, doubles wins are worth 2 points
            league = request.args.get('league', '')
            if league == 'riksserien':
                sub_wins_expr1 = "(SELECT COALESCE(SUM(CASE WHEN sm.match_type = 'Doubles' THEN 2 ELSE 1 END), 0) FROM sub_matches sm WHERE sm.match_id = m.id AND sm.team1_legs > sm.team2_legs)"
                sub_wins_expr2 = "(SELECT COALESCE(SUM(CASE WHEN sm.match_type = 'Doubles' THEN 2 ELSE 1 END), 0) FROM sub_matches sm WHERE sm.match_id = m.id AND sm.team2_legs > sm.team1_legs)"
            else:
                sub_wins_expr1 = "(SELECT COUNT(*) FROM sub_matches sm WHERE sm.match_id = m.id AND sm.team1_legs > sm.team2_legs)"
                sub_wins_expr2 = "(SELECT COUNT(*) FROM sub_matches sm WHERE sm.match_id = m.id AND sm.team2_legs > sm.team1_legs)"

            # Exclude matches where no sub-match has been decided (0-0)
            no_result_filter = f"({sub_wins_expr1} + {sub_wins_expr2}) > 0"
            if where_sql:
                where_sql += f" AND {no_result_filter}"
            else:
                where_sql = f"WHERE {no_result_filter}"

            cursor.execute(f"""
                SELECT
                    m.id,
                    m.match_date,
                    m.season,
                    m.division,
                    t1.name as team1_name,
                    t2.name as team2_name,
                    m.team1_score,
                    m.team2_score,
                    {sub_wins_expr1} as team1_sub_wins,
                    {sub_wins_expr2} as team2_sub_wins
                FROM matches m
                JOIN teams t1 ON m.team1_id = t1.id
                JOIN teams t2 ON m.team2_id = t2.id
                {where_sql}
                ORDER BY m.match_date DESC, m.id DESC
            """, params)

            matches = cursor.fetchall()

            # Get available seasons and divisions for filters
            cursor.execute("SELECT DISTINCT season FROM matches ORDER BY season DESC")
            seasons = [row['season'] for row in cursor.fetchall()]

            cursor.execute("SELECT DISTINCT division FROM matches ORDER BY division")
            divisions = [row['division'] for row in cursor.fetchall()]

            # Group matches by week
            matches_by_week = {}
            for match in matches:
                match_dict = dict(match)
                match_date = match['match_date']

                if match_date:
                    # Parse date and get ISO week - extract just the date part
                    try:
                        # Handle various formats by extracting YYYY-MM-DD part
                        date_str = str(match_date).split('T')[0].split(' ')[0]
                        dt = datetime.strptime(date_str, '%Y-%m-%d')
                        year, week, _ = dt.isocalendar()
                        week_key = f"{year}-W{week:02d}"
                        week_label = f"Vecka {week}, {year}"
                    except Exception:
                        week_key = "unknown"
                        week_label = "Okant datum"
                else:
                    week_key = "unknown"
                    week_label = "Okant datum"

                if week_key not in matches_by_week:
                    matches_by_week[week_key] = {
                        'week_key': week_key,
                        'week_label': week_label,
                        'matches': []
                    }

                matches_by_week[week_key]['matches'].append(match_dict)

            # Sort weeks descending and convert to list
            sorted_weeks = sorted(matches_by_week.values(),
                                  key=lambda x: x['week_key'],
                                  reverse=True)

            return jsonify({
                'weeks': sorted_weeks,
                'seasons': seasons,
                'divisions': divisions,
                'current_season': season,
                'current_division': division
            })

    except Exception as e:
        return jsonify({'error': str(e)}), 500
