import re
import sqlite3
from collections import defaultdict
from flask import Blueprint, request, jsonify

teams_bp = Blueprint('teams', __name__)


def _get_current_db_path():
    from app import get_current_db_path
    return get_current_db_path()


@teams_bp.route('/api/team/<path:team_name>/lineup')
def get_team_lineup(team_name):
    """Get team lineup prediction based on historical position data"""
    try:
        with sqlite3.connect(_get_current_db_path()) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # Get filter parameters
            season = request.args.get('season')
            division = None

            # Handle new team name format: "Team (Division) (Season)" or "Team Name (Season)"
            # Try new format first: "Team (Division) (YYYY-YYYY)"
            new_format_match = re.search(r'^(.+?)\s+\(([^)]+)\)\s+\((\d{4}-\d{4})\)$', team_name)
            if new_format_match:
                # Extract team, division, and season from new format
                base_team_name = new_format_match.group(1)
                division_from_name = new_format_match.group(2)
                season = new_format_match.group(3).replace('-', '/')  # Convert back to 2024/2025 format

                # Try to find team with division in name, but verify it has matches in the season
                team_name_with_division = f"{base_team_name} ({division_from_name})"
                cursor.execute("""
                    SELECT t.id FROM teams t
                    JOIN matches m ON t.id = m.team1_id OR t.id = m.team2_id
                    WHERE t.name = ? AND m.season = ?
                    LIMIT 1
                """, (team_name_with_division, season))
                team_with_div_result = cursor.fetchone()

                if team_with_div_result:
                    # Use team with division in name
                    team_name = team_name_with_division
                    division = None
                    team_result = team_with_div_result
                else:
                    # Fallback: try base team name with division filter
                    cursor.execute("SELECT id FROM teams WHERE name = ?", (base_team_name,))
                    base_result = cursor.fetchone()

                    if base_result:
                        # Team exists without division in name, use division filter
                        team_name = base_team_name
                        division = division_from_name
                        team_result = base_result
                    else:
                        # Team not found
                        team_result = None
            else:
                # Try old format: "Team Name (YYYY-YYYY)"
                old_format_match = re.search(r'^(.+)\s+\((\d{4}-\d{4})\)$', team_name)
                if old_format_match:
                    team_name = old_format_match.group(1)
                    season = old_format_match.group(2).replace('-', '/')
                    division = None
                else:
                    # No season in team name
                    season = request.args.get('season')

            # Final check if team exists (if not already done above)
            if 'team_result' not in locals():
                print(f"DEBUG: Looking for team: '{team_name}'", flush=True)
                cursor.execute("SELECT id FROM teams WHERE name = ?", (team_name,))
                team_result = cursor.fetchone()
                if not team_result:
                    # Debug: show similar team names
                    cursor.execute("SELECT name FROM teams WHERE name LIKE ? LIMIT 10", (f"%{team_name.split()[0]}%",))
                    similar_teams = cursor.fetchall()
                    print(f"DEBUG: Similar teams found: {[t[0] for t in similar_teams]}", flush=True)
            if not team_result:
                return jsonify({'error': f'Lag hittades inte: {team_name}'}), 404

            team_id = team_result['id']

            # Build WHERE clause for filtering
            where_conditions = ["(m.team1_id = ? OR m.team2_id = ?)"]
            params = [team_id, team_id]

            if season:
                where_conditions.append("m.season = ?")
                params.append(season)

            if division:
                where_conditions.append("m.division = ?")
                params.append(division)

            where_clause = " AND ".join(where_conditions)

            # Get position analysis for this team
            cursor.execute(f"""
                WITH position_data AS (
                    SELECT
                        p.name as player_name,
                        sm.match_name,
                        sm.match_type,
                        smp.team_number,
                        CASE WHEN smp.team_number = 1 THEN t1.name ELSE t2.name END as player_team,
                        COUNT(*) as matches_in_position
                    FROM sub_match_participants smp
                    JOIN players p ON smp.player_id = p.id
                    JOIN sub_matches sm ON smp.sub_match_id = sm.id
                    JOIN matches m ON sm.match_id = m.id
                    JOIN teams t1 ON m.team1_id = t1.id
                    JOIN teams t2 ON m.team2_id = t2.id
                    WHERE {where_clause}
                      AND (CASE WHEN smp.team_number = 1 THEN t1.name ELSE t2.name END) = ?
                    GROUP BY p.name, sm.match_name, sm.match_type
                ),
                position_stats AS (
                    SELECT
                        player_name,
                        CASE
                            WHEN match_name LIKE '% AD%' OR match_name LIKE '%AD' THEN 'AD'
                            WHEN match_name LIKE '% Singles1%' THEN 'S1'
                            WHEN match_name LIKE '% Singles2%' THEN 'S2'
                            WHEN match_name LIKE '% Singles3%' THEN 'S3'
                            WHEN match_name LIKE '% Singles4%' THEN 'S4'
                            WHEN match_name LIKE '% Singles5%' THEN 'S5'
                            WHEN match_name LIKE '% Singles6%' THEN 'S6'
                            WHEN match_name LIKE '% Doubles1%' THEN 'D1'
                            WHEN match_name LIKE '% Doubles2%' THEN 'D2'
                            WHEN match_name LIKE '% Doubles3%' THEN 'D3'
                            ELSE 'Unknown'
                        END as position,
                        SUM(matches_in_position) as total_matches
                    FROM position_data
                    GROUP BY player_name, position
                    HAVING position != 'Unknown'
                )
                SELECT
                    position,
                    player_name,
                    total_matches,
                    ROW_NUMBER() OVER (PARTITION BY position ORDER BY total_matches DESC) as rank
                FROM position_stats
                ORDER BY position, total_matches DESC
            """, params + [team_name])

            position_data = cursor.fetchall()

            # Get total team matches for percentage calculation
            cursor.execute(f"""
                SELECT COUNT(DISTINCT m.id) as total_team_matches
                FROM matches m
                WHERE {where_clause}
            """, params)

            total_matches = cursor.fetchone()['total_team_matches']

            # Organize data by position
            positions = {}
            for row in position_data:
                position = row['position']
                if position not in positions:
                    positions[position] = {'players': [], 'total_position_matches': 0}

                # Calculate percentage for this position
                percentage = round((row['total_matches'] / total_matches) * 100, 1) if total_matches > 0 else 0

                player_data = {
                    'name': row['player_name'],
                    'matches': row['total_matches'],
                    'percentage': percentage,
                    'rank': row['rank']
                }

                positions[position]['players'].append(player_data)
                positions[position]['total_position_matches'] += row['total_matches']

            # Format response for frontend
            formatted_positions = {}
            for pos, data in positions.items():
                if pos.startswith('S'):  # Singles positions
                    formatted_positions[pos] = {
                        'top_player': data['players'][0] if data['players'] else None,
                        'all_players': data['players']
                    }
                else:  # Doubles positions (including AD)
                    # For doubles, we might want to show partnerships
                    formatted_positions[pos] = {
                        'players': data['players'][:3],  # Top 3 players for this position
                        'total_matches': data['total_position_matches']
                    }

            # If division is still unknown, look it up from matches
            if not division:
                div_params = [team_id, team_id]
                div_where = "(m.team1_id = ? OR m.team2_id = ?)"
                if season:
                    div_where += " AND m.season = ?"
                    div_params.append(season)
                cursor.execute(f"""
                    SELECT DISTINCT m.division FROM matches m
                    WHERE {div_where} AND m.division IS NOT NULL AND m.division != 'Unknown'
                """, div_params)
                div_rows = [r['division'] for r in cursor.fetchall()]
                if len(div_rows) == 1:
                    division = div_rows[0]
                elif len(div_rows) > 1:
                    division = ', '.join(div_rows)

            return jsonify({
                'team_name': team_name,
                'total_matches': total_matches,
                'season': season,
                'division': division,
                'positions': formatted_positions
            })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@teams_bp.route('/api/team/<path:team_name>/players')
def get_team_players(team_name):
    """Get all players who have played for a team"""
    try:
        with sqlite3.connect(_get_current_db_path()) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # Get filter parameters
            season = request.args.get('season')
            division = None

            # Handle team name format with season/division
            # Try new format first: "Team (Division) (YYYY-YYYY)"
            new_format_match = re.search(r'^(.+?)\s+\(([^)]+)\)\s+\((\d{4}-\d{4})\)$', team_name)
            if new_format_match:
                base_team_name = new_format_match.group(1)
                division_from_name = new_format_match.group(2)
                season = new_format_match.group(3).replace('-', '/')

                # Try with division in name first, but verify it has matches in the season
                team_name_with_division = f"{base_team_name} ({division_from_name})"
                cursor.execute("""
                    SELECT t.id FROM teams t
                    JOIN matches m ON t.id = m.team1_id OR t.id = m.team2_id
                    WHERE t.name = ? AND m.season = ?
                    LIMIT 1
                """, (team_name_with_division, season))
                team_result = cursor.fetchone()

                if team_result:
                    team_name = team_name_with_division
                    # Don't use division filter - teams may be registered in different divisions
                    # even though the team name contains a division
                    division = None
                else:
                    # Team with division in name doesn't have matches in this season,
                    # try base team with division filter
                    team_name = base_team_name
                    division = division_from_name
            else:
                # Try old format: "Team Name (YYYY-YYYY)"
                old_format_match = re.search(r'^(.+)\s+\((\d{4}-\d{4})\)$', team_name)
                if old_format_match:
                    team_name = old_format_match.group(1)
                    season = old_format_match.group(2).replace('-', '/')

            # Get team ID
            cursor.execute("SELECT id FROM teams WHERE name = ?", (team_name,))
            team_result = cursor.fetchone()
            if not team_result:
                return jsonify({'error': f'Lag hittades inte: {team_name}'}), 404

            team_id = team_result['id']

            # Build WHERE clause for filtering
            where_conditions = ["(m.team1_id = ? OR m.team2_id = ?)"]
            params = [team_id, team_id]

            if season:
                where_conditions.append("m.season = ?")
                params.append(season)

            if division:
                where_conditions.append("m.division = ?")
                params.append(division)

            where_clause = " AND ".join(where_conditions)

            # Get all players who have played for this team with singles/doubles breakdown, average, and win/loss
            cursor.execute(f"""
                WITH player_data AS (
                    SELECT
                        p.id as player_id,
                        COALESCE(smpm.correct_player_name, p.name) as player_name,
                        sm.id as sub_match_id,
                        sm.match_name,
                        CASE
                            WHEN sm.match_name LIKE '% AD' OR sm.match_name LIKE '% AD %' THEN 'Doubles'
                            ELSE sm.match_type
                        END as corrected_match_type,
                        m.id as match_id,
                        m.season,
                        smp.team_number,
                        smp.player_avg
                    FROM sub_match_participants smp
                    JOIN players p ON smp.player_id = p.id
                    JOIN sub_matches sm ON smp.sub_match_id = sm.id
                    JOIN matches m ON sm.match_id = m.id
                    JOIN teams t1 ON m.team1_id = t1.id
                    JOIN teams t2 ON m.team2_id = t2.id
                    LEFT JOIN sub_match_player_mappings smpm
                        ON smpm.sub_match_id = smp.sub_match_id AND smpm.original_player_id = p.id
                    WHERE {where_clause}
                      AND (CASE WHEN smp.team_number = 1 THEN t1.name ELSE t2.name END) = ?
                ),
                sub_match_results AS (
                    SELECT
                        pd.player_id,
                        pd.player_name,
                        pd.sub_match_id,
                        pd.corrected_match_type,
                        pd.match_id,
                        pd.season,
                        pd.team_number,
                        pd.player_avg,
                        SUM(CASE WHEN legs.winner_team = pd.team_number THEN 1 ELSE 0 END) as player_legs_won,
                        SUM(CASE WHEN legs.winner_team != pd.team_number AND legs.winner_team IS NOT NULL THEN 1 ELSE 0 END) as player_legs_lost
                    FROM player_data pd
                    LEFT JOIN legs ON legs.sub_match_id = pd.sub_match_id
                    GROUP BY pd.player_id, pd.player_name, pd.sub_match_id, pd.corrected_match_type, pd.match_id, pd.season, pd.team_number, pd.player_avg
                )
                SELECT
                    player_name,
                    player_id,
                    COUNT(DISTINCT match_id) as matches_played,
                    COUNT(DISTINCT CASE WHEN corrected_match_type = 'Singles' THEN sub_match_id END) as singles_played,
                    COUNT(DISTINCT CASE WHEN corrected_match_type = 'Doubles' THEN sub_match_id END) as doubles_played,
                    COUNT(DISTINCT sub_match_id) as sub_matches_played,
                    SUM(CASE WHEN player_legs_won > player_legs_lost THEN 1 ELSE 0 END) as sub_matches_won,
                    SUM(CASE WHEN player_legs_won < player_legs_lost THEN 1 ELSE 0 END) as sub_matches_lost,
                    SUM(CASE WHEN corrected_match_type = 'Singles' AND player_legs_won > player_legs_lost THEN 1 ELSE 0 END) as singles_won,
                    SUM(CASE WHEN corrected_match_type = 'Doubles' AND player_legs_won > player_legs_lost THEN 1 ELSE 0 END) as doubles_won,
                    GROUP_CONCAT(DISTINCT season) as seasons
                FROM sub_match_results
                WHERE player_name IS NOT NULL AND player_name != ''
                GROUP BY player_name
                ORDER BY matches_played DESC, player_name ASC
            """, params + [team_name])

            players = []
            for row in cursor.fetchall():
                player_id = row['player_id']
                player_name = row['player_name']

                # Calculate weighted average for singles matches only
                # Use the same method as database.py get_player_stats
                # Include both direct matches and mapped sub-matches
                singles_avg = None
                if row['singles_played'] > 0:
                    # Get singles matches for this player (including mapped)
                    cursor.execute(f"""
                        SELECT DISTINCT sm.id as sub_match_id, smp.player_avg, smp.team_number
                        FROM sub_match_participants smp
                        JOIN sub_matches sm ON smp.sub_match_id = sm.id
                        JOIN matches m ON sm.match_id = m.id
                        JOIN teams t1 ON m.team1_id = t1.id
                        JOIN teams t2 ON m.team2_id = t2.id
                        LEFT JOIN sub_match_player_mappings smpm
                            ON smpm.sub_match_id = smp.sub_match_id AND smpm.original_player_id = smp.player_id
                        WHERE (
                            -- Direct matches for this player
                            (smp.player_id = ? AND smpm.id IS NULL)
                            OR
                            -- Sub-matches mapped TO this player name
                            (smpm.correct_player_name = ?)
                        )
                          AND {where_clause}
                          AND (CASE WHEN smp.team_number = 1 THEN t1.name ELSE t2.name END) = ?
                          AND CASE
                              WHEN sm.match_name LIKE '% AD' OR sm.match_name LIKE '% AD %' THEN 'Doubles'
                              ELSE sm.match_type
                          END = 'Singles'
                          AND smp.player_avg > 0
                    """, [player_id, player_name] + params + [team_name])

                    singles_matches = cursor.fetchall()

                    # Calculate weighted average
                    total_score = 0.0
                    total_darts = 0

                    for match in singles_matches:
                        sub_match_id = match['sub_match_id']
                        player_avg = match['player_avg']
                        team_number = match['team_number']

                        # Count darts for this match (same logic as database.py)
                        cursor.execute('''
                            SELECT l.leg_number, t.score, t.darts_used, t.remaining_score
                            FROM legs l
                            JOIN throws t ON t.leg_id = l.id
                            WHERE l.sub_match_id = ? AND t.team_number = ?
                            ORDER BY l.leg_number, t.id
                        ''', (sub_match_id, team_number))

                        all_throws = cursor.fetchall()
                        match_darts = 0
                        last_remaining = {}

                        for throw in all_throws:
                            leg_num = throw['leg_number']
                            score = throw['score']
                            darts_used = throw['darts_used']
                            remaining = throw['remaining_score']

                            # Skip starting throw
                            if score == 0 and remaining == 501:
                                continue

                            if remaining == 0:
                                # Checkout
                                if score <= 3:
                                    checkout_darts = score if score else 3
                                else:
                                    checkout_darts = darts_used if darts_used else 3
                                match_darts += checkout_darts
                            else:
                                match_darts += (darts_used if darts_used else 3)
                                if score > 0:
                                    last_remaining[leg_num] = remaining

                        match_score = (player_avg * match_darts) / 3.0
                        total_score += match_score
                        total_darts += match_darts

                    if total_darts > 0:
                        singles_avg = round((total_score / total_darts * 3.0), 2)

                singles_played = row['singles_played']
                doubles_played = row['doubles_played']
                singles_won = row['singles_won']
                doubles_won = row['doubles_won']

                singles_win_pct = round((singles_won / singles_played * 100), 0) if singles_played > 0 else 0
                doubles_win_pct = round((doubles_won / doubles_played * 100), 0) if doubles_played > 0 else 0

                players.append({
                    'name': player_name,
                    'matches_played': row['matches_played'],
                    'sub_matches_played': row['sub_matches_played'],
                    'singles_played': singles_played,
                    'doubles_played': doubles_played,
                    'singles_won': singles_won,
                    'doubles_won': doubles_won,
                    'singles_win_pct': singles_win_pct,
                    'doubles_win_pct': doubles_win_pct,
                    'sub_matches_won': row['sub_matches_won'],
                    'sub_matches_lost': row['sub_matches_lost'],
                    'average': singles_avg,
                    'seasons': row['seasons']
                })

            # Get total team matches
            cursor.execute(f"""
                SELECT COUNT(DISTINCT m.id) as total_team_matches
                FROM matches m
                WHERE {where_clause}
            """, params)

            total_matches = cursor.fetchone()['total_team_matches']

            # Sort players by singles_played (desc), then by average (desc, None last)
            players.sort(key=lambda p: (
                -p['singles_played'],
                -(p['average'] if p['average'] is not None else -float('inf'))
            ))

            # If division is still unknown, look it up from matches
            if not division:
                div_params = [team_id, team_id]
                div_where = "(m.team1_id = ? OR m.team2_id = ?)"
                if season:
                    div_where += " AND m.season = ?"
                    div_params.append(season)
                cursor.execute(f"""
                    SELECT DISTINCT m.division FROM matches m
                    WHERE {div_where} AND m.division IS NOT NULL AND m.division != 'Unknown'
                """, div_params)
                div_rows = [r['division'] for r in cursor.fetchall()]
                if len(div_rows) == 1:
                    division = div_rows[0]
                elif len(div_rows) > 1:
                    division = ', '.join(div_rows)

            return jsonify({
                'team_name': team_name,
                'total_matches': total_matches,
                'season': season,
                'division': division,
                'players': players,
                'player_count': len(players)
            })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@teams_bp.route('/api/team/<path:team_name>/doubles-pairs')
def get_team_doubles_pairs(team_name):
    """Get doubles pair statistics for a team - who played with whom and at which position"""
    try:
        with sqlite3.connect(_get_current_db_path()) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            season = request.args.get('season')
            division_param = request.args.get('division')

            # Handle team name format with season/division
            division = division_param  # Use parameter if provided
            new_format_match = re.search(r'^(.+?)\s+\(([^)]+)\)\s+\((\d{4}-\d{4})\)$', team_name)
            if new_format_match:
                base_team_name = new_format_match.group(1)
                division_from_name = new_format_match.group(2)
                season = new_format_match.group(3).replace('-', '/')
                team_name_with_division = f"{base_team_name} ({division_from_name})"
                # Verify team has matches in this season before using it
                cursor.execute("""
                    SELECT t.id FROM teams t
                    JOIN matches m ON t.id = m.team1_id OR t.id = m.team2_id
                    WHERE t.name = ? AND m.season = ?
                    LIMIT 1
                """, (team_name_with_division, season))
                team_result = cursor.fetchone()
                if team_result:
                    team_name = team_name_with_division
                else:
                    team_name = base_team_name
                    if not division:  # Only set if not already provided
                        division = division_from_name
            else:
                old_format_match = re.search(r'^(.+)\s+\((\d{4}-\d{4})\)$', team_name)
                if old_format_match:
                    team_name = old_format_match.group(1)
                    season = old_format_match.group(2).replace('-', '/')

            # Get team ID
            cursor.execute("SELECT id FROM teams WHERE name = ?", (team_name,))
            team_result = cursor.fetchone()
            if not team_result:
                return jsonify({'error': f'Lag hittades inte: {team_name}'}), 404

            team_id = team_result['id']

            # Build WHERE clause
            where_conditions = ["(m.team1_id = ? OR m.team2_id = ?)"]
            params = [team_id, team_id]

            if season:
                where_conditions.append("m.season = ?")
                params.append(season)

            if division:
                where_conditions.append("m.division = ?")
                params.append(division)

            where_clause = " AND ".join(where_conditions)

            # Get all doubles matches for this team with both players
            cursor.execute(f"""
                SELECT
                    sm.id as sub_match_id,
                    sm.match_name,
                    m.match_date,
                    m.season,
                    smp.team_number,
                    smp.player_id,
                    COALESCE(smpm.correct_player_name, p.name) as player_name,
                    CASE WHEN smp.team_number = 1 THEN t1.name ELSE t2.name END as player_team,
                    (SELECT SUM(CASE WHEN legs.winner_team = smp.team_number THEN 1 ELSE 0 END) >
                            SUM(CASE WHEN legs.winner_team != smp.team_number AND legs.winner_team IS NOT NULL THEN 1 ELSE 0 END)
                     FROM legs WHERE legs.sub_match_id = sm.id) as won
                FROM sub_match_participants smp
                JOIN players p ON smp.player_id = p.id
                JOIN sub_matches sm ON smp.sub_match_id = sm.id
                JOIN matches m ON sm.match_id = m.id
                JOIN teams t1 ON m.team1_id = t1.id
                JOIN teams t2 ON m.team2_id = t2.id
                LEFT JOIN sub_match_player_mappings smpm
                    ON smpm.sub_match_id = smp.sub_match_id AND smpm.original_player_id = p.id
                WHERE {where_clause}
                  AND (CASE WHEN smp.team_number = 1 THEN t1.name ELSE t2.name END) = ?
                  AND (sm.match_type = 'Doubles' OR sm.match_name LIKE '% AD' OR sm.match_name LIKE '% AD %')
                ORDER BY sm.id, smp.player_id
            """, params + [team_name])

            rows = cursor.fetchall()

            # Group by sub_match to find pairs
            sub_matches = defaultdict(list)
            for row in rows:
                sub_matches[row['sub_match_id']].append({
                    'player_name': row['player_name'],
                    'match_name': row['match_name'],
                    'won': row['won'],
                    'match_date': row['match_date']
                })

            # Extract position from match_name
            def get_position(match_name):
                if ' Doubles1' in match_name or match_name.endswith(' D1'):
                    return 'D1'
                elif ' Doubles2' in match_name or match_name.endswith(' D2'):
                    return 'D2'
                elif ' Doubles3' in match_name or match_name.endswith(' D3'):
                    return 'D3'
                elif ' AD' in match_name:
                    return 'AD'
                return 'D'

            # Build pair statistics
            pair_stats = defaultdict(lambda: {'total': 0, 'wins': 0, 'positions': defaultdict(int)})
            player_pairs = defaultdict(lambda: defaultdict(lambda: {'total': 0, 'wins': 0, 'positions': defaultdict(int)}))

            for sub_match_id, players in sub_matches.items():
                if len(players) >= 2:
                    # Filter out empty names
                    valid_players = [p for p in players if p['player_name'] and p['player_name'].strip()]
                    if len(valid_players) >= 2:
                        p1, p2 = sorted([valid_players[0]['player_name'], valid_players[1]['player_name']])
                        position = get_position(valid_players[0]['match_name'])
                        won = valid_players[0]['won']

                        pair_key = f"{p1} + {p2}"
                        pair_stats[pair_key]['total'] += 1
                        pair_stats[pair_key]['positions'][position] += 1
                        if won:
                            pair_stats[pair_key]['wins'] += 1

                        # Track per player
                        player_pairs[valid_players[0]['player_name']][valid_players[1]['player_name']]['total'] += 1
                        player_pairs[valid_players[0]['player_name']][valid_players[1]['player_name']]['positions'][position] += 1
                        if won:
                            player_pairs[valid_players[0]['player_name']][valid_players[1]['player_name']]['wins'] += 1

                        player_pairs[valid_players[1]['player_name']][valid_players[0]['player_name']]['total'] += 1
                        player_pairs[valid_players[1]['player_name']][valid_players[0]['player_name']]['positions'][position] += 1
                        if won:
                            player_pairs[valid_players[1]['player_name']][valid_players[0]['player_name']]['wins'] += 1

            # Format output - per player view
            players_data = []
            for player, partners in sorted(player_pairs.items()):
                partner_list = []
                total_positions = defaultdict(int)
                for partner, stats in sorted(partners.items(), key=lambda x: -x[1]['total']):
                    win_pct = round(stats['wins'] / stats['total'] * 100) if stats['total'] > 0 else 0
                    partner_list.append({
                        'partner': partner,
                        'total': stats['total'],
                        'wins': stats['wins'],
                        'win_pct': win_pct,
                        'positions': dict(stats['positions'])
                    })
                    # Aggregate positions for the player
                    for pos, count in stats['positions'].items():
                        total_positions[pos] += count

                # Each partner entry already represents unique matches, so no need to divide
                # But filter out zero values
                player_positions = {pos: count for pos, count in total_positions.items() if count > 0}

                players_data.append({
                    'player': player,
                    'total_doubles': sum(p['total'] for p in partner_list),
                    'positions': player_positions,
                    'partners': partner_list
                })

            # Sort by total doubles played
            players_data.sort(key=lambda x: -x['total_doubles'])

            # Format pairs view
            pairs_list = []
            for pair_key, stats in sorted(pair_stats.items(), key=lambda x: -x[1]['total']):
                win_pct = round(stats['wins'] / stats['total'] * 100) if stats['total'] > 0 else 0
                pairs_list.append({
                    'pair': pair_key,
                    'total': stats['total'],
                    'wins': stats['wins'],
                    'win_pct': win_pct,
                    'positions': dict(stats['positions'])
                })

            return jsonify({
                'team_name': team_name,
                'season': season,
                'players': players_data,
                'pairs': pairs_list,
                'total_doubles_matches': len([sm for sm in sub_matches.values() if len(sm) >= 2])
            })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@teams_bp.route('/api/club/<path:club_name>/players')
def get_club_players(club_name):
    """Get all players who have played for any team in a club (across all divisions)"""
    try:
        with sqlite3.connect(_get_current_db_path()) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            season = request.args.get('season')

            # Extract base club name (remove division suffix if present)
            # "Mitt i DC (3FD)" -> "Mitt i DC"
            base_club = re.sub(r'\s*\([^)]*\)$', '', club_name).strip()

            # Find all teams for this club
            cursor.execute("SELECT id, name FROM teams WHERE name = ? OR name LIKE ?",
                          (base_club, f"{base_club} (%)",))
            club_teams = cursor.fetchall()

            if not club_teams:
                return jsonify({'error': f'Klubb hittades inte: {base_club}'}), 404

            team_ids = [t['id'] for t in club_teams]
            team_names = [t['name'] for t in club_teams]

            # Build WHERE clause
            team_placeholders = ','.join(['?' for _ in team_ids])
            where_conditions = [f"(m.team1_id IN ({team_placeholders}) OR m.team2_id IN ({team_placeholders}))"]
            params = team_ids + team_ids

            if season:
                where_conditions.append("m.season = ?")
                params.append(season)

            where_clause = " AND ".join(where_conditions)

            # Build team name match condition
            team_name_placeholders = ','.join(['?' for _ in team_names])

            cursor.execute(f"""
                WITH player_data AS (
                    SELECT
                        p.id as player_id,
                        COALESCE(smpm.correct_player_name, p.name) as player_name,
                        sm.id as sub_match_id,
                        sm.match_name,
                        CASE
                            WHEN sm.match_name LIKE '% AD' OR sm.match_name LIKE '% AD %' THEN 'Doubles'
                            ELSE sm.match_type
                        END as corrected_match_type,
                        m.id as match_id,
                        m.season,
                        smp.team_number,
                        smp.player_avg,
                        CASE WHEN smp.team_number = 1 THEN t1.name ELSE t2.name END as player_team
                    FROM sub_match_participants smp
                    JOIN players p ON smp.player_id = p.id
                    JOIN sub_matches sm ON smp.sub_match_id = sm.id
                    JOIN matches m ON sm.match_id = m.id
                    JOIN teams t1 ON m.team1_id = t1.id
                    JOIN teams t2 ON m.team2_id = t2.id
                    LEFT JOIN sub_match_player_mappings smpm
                        ON smpm.sub_match_id = smp.sub_match_id AND smpm.original_player_id = p.id
                    WHERE {where_clause}
                      AND (CASE WHEN smp.team_number = 1 THEN t1.name ELSE t2.name END) IN ({team_name_placeholders})
                ),
                sub_match_results AS (
                    SELECT
                        pd.player_id,
                        pd.player_name,
                        pd.sub_match_id,
                        pd.corrected_match_type,
                        pd.match_id,
                        pd.season,
                        pd.team_number,
                        pd.player_avg,
                        pd.player_team,
                        SUM(CASE WHEN legs.winner_team = pd.team_number THEN 1 ELSE 0 END) as player_legs_won,
                        SUM(CASE WHEN legs.winner_team != pd.team_number AND legs.winner_team IS NOT NULL THEN 1 ELSE 0 END) as player_legs_lost
                    FROM player_data pd
                    LEFT JOIN legs ON legs.sub_match_id = pd.sub_match_id
                    GROUP BY pd.player_id, pd.player_name, pd.sub_match_id, pd.corrected_match_type, pd.match_id, pd.season, pd.team_number, pd.player_avg, pd.player_team
                )
                SELECT
                    player_name,
                    player_id,
                    COUNT(DISTINCT match_id) as matches_played,
                    COUNT(DISTINCT CASE WHEN corrected_match_type = 'Singles' THEN sub_match_id END) as singles_played,
                    COUNT(DISTINCT CASE WHEN corrected_match_type = 'Doubles' THEN sub_match_id END) as doubles_played,
                    COUNT(DISTINCT sub_match_id) as sub_matches_played,
                    SUM(CASE WHEN player_legs_won > player_legs_lost THEN 1 ELSE 0 END) as sub_matches_won,
                    SUM(CASE WHEN player_legs_won < player_legs_lost THEN 1 ELSE 0 END) as sub_matches_lost,
                    SUM(CASE WHEN corrected_match_type = 'Singles' AND player_legs_won > player_legs_lost THEN 1 ELSE 0 END) as singles_won,
                    SUM(CASE WHEN corrected_match_type = 'Doubles' AND player_legs_won > player_legs_lost THEN 1 ELSE 0 END) as doubles_won,
                    GROUP_CONCAT(DISTINCT season) as seasons,
                    GROUP_CONCAT(DISTINCT player_team) as teams_played_for
                FROM sub_match_results
                WHERE player_name IS NOT NULL AND player_name != ''
                GROUP BY player_name
                ORDER BY matches_played DESC, player_name ASC
            """, params + team_names)

            players = []
            for row in cursor.fetchall():
                player_id = row['player_id']
                player_name = row['player_name']

                # Calculate weighted average for singles matches
                # Include both direct matches and mapped sub-matches
                singles_avg = None
                if row['singles_played'] > 0:
                    cursor.execute(f"""
                        SELECT DISTINCT sm.id as sub_match_id, smp.player_avg, smp.team_number
                        FROM sub_match_participants smp
                        JOIN sub_matches sm ON smp.sub_match_id = sm.id
                        JOIN matches m ON sm.match_id = m.id
                        JOIN teams t1 ON m.team1_id = t1.id
                        JOIN teams t2 ON m.team2_id = t2.id
                        LEFT JOIN sub_match_player_mappings smpm
                            ON smpm.sub_match_id = smp.sub_match_id AND smpm.original_player_id = smp.player_id
                        WHERE (
                            -- Direct matches for this player
                            (smp.player_id = ? AND smpm.id IS NULL)
                            OR
                            -- Sub-matches mapped TO this player name
                            (smpm.correct_player_name = ?)
                        )
                          AND {where_clause}
                          AND (CASE WHEN smp.team_number = 1 THEN t1.name ELSE t2.name END) IN ({team_name_placeholders})
                          AND CASE
                              WHEN sm.match_name LIKE '% AD' OR sm.match_name LIKE '% AD %' THEN 'Doubles'
                              ELSE sm.match_type
                          END = 'Singles'
                          AND smp.player_avg > 0
                    """, [player_id, player_name] + params + team_names)

                    singles_matches = cursor.fetchall()
                    total_score = 0.0
                    total_darts = 0

                    for match in singles_matches:
                        sub_match_id = match['sub_match_id']
                        player_avg = match['player_avg']
                        team_number = match['team_number']

                        cursor.execute('''
                            SELECT l.leg_number, t.score, t.darts_used, t.remaining_score
                            FROM legs l
                            JOIN throws t ON t.leg_id = l.id
                            WHERE l.sub_match_id = ? AND t.team_number = ?
                            ORDER BY l.leg_number, t.id
                        ''', (sub_match_id, team_number))

                        all_throws = cursor.fetchall()
                        match_darts = 0

                        for throw in all_throws:
                            score = throw['score']
                            darts_used = throw['darts_used']
                            remaining = throw['remaining_score']

                            # Skip starting throw (score=0, remaining=501)
                            if score == 0 and remaining == 501:
                                continue

                            if remaining == 0:
                                # Checkout - detect format based on score value
                                if score <= 3:
                                    checkout_darts = score if score else 3
                                else:
                                    checkout_darts = darts_used if darts_used else 3
                                match_darts += checkout_darts
                            else:
                                # Regular throw
                                match_darts += (darts_used if darts_used else 3)

                        if match_darts > 0:
                            match_score = (player_avg * match_darts) / 3.0
                            total_score += match_score
                            total_darts += match_darts

                    if total_darts > 0:
                        singles_avg = round((total_score / total_darts * 3.0), 2)

                singles_win_pct = round(row['singles_won'] / row['singles_played'] * 100) if row['singles_played'] > 0 else 0
                doubles_win_pct = round(row['doubles_won'] / row['doubles_played'] * 100) if row['doubles_played'] > 0 else 0

                # Extract just division names from teams_played_for
                # "Mitt i DC (3FD),Mitt i DC (2A)" -> "3FD, 2A"
                # Sort: Superligan, SL6, SL4 first, then rest ascending
                divisions_played = None
                if row['teams_played_for']:
                    divisions = []
                    for team in row['teams_played_for'].split(','):
                        match = re.search(r'\(([^)]+)\)$', team.strip())
                        if match:
                            divisions.append(match.group(1))
                    if divisions:
                        unique_divs = set(divisions)
                        priority = ['Superligan', 'SL6', 'SL4']
                        priority_divs = [d for d in priority if d in unique_divs]
                        other_divs = sorted([d for d in unique_divs if d not in priority])
                        divisions_played = ', '.join(priority_divs + other_divs)

                players.append({
                    'name': player_name,
                    'matches_played': row['matches_played'],
                    'singles_played': row['singles_played'],
                    'doubles_played': row['doubles_played'],
                    'singles_won': row['singles_won'],
                    'doubles_won': row['doubles_won'],
                    'singles_win_pct': singles_win_pct,
                    'doubles_win_pct': doubles_win_pct,
                    'average': singles_avg,
                    'seasons': row['seasons'],
                    'divisions_played': divisions_played
                })

            # Get total matches across all club teams
            cursor.execute(f"""
                SELECT COUNT(DISTINCT m.id) as total_club_matches
                FROM matches m
                WHERE {where_clause}
            """, params)

            total_matches = cursor.fetchone()['total_club_matches']

            # Sort players by singles_played (desc), then by average (desc, None last)
            players.sort(key=lambda p: (
                -p['singles_played'],
                -(p['average'] if p['average'] is not None else -float('inf'))
            ))

            return jsonify({
                'club_name': base_club,
                'teams': team_names,
                'total_matches': total_matches,
                'season': season,
                'players': players,
                'player_count': len(players)
            })

    except Exception as e:
        return jsonify({'error': str(e)}), 500
