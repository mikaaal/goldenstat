import sqlite3
from collections import defaultdict, Counter
from flask import Blueprint, request, jsonify, render_template

players_bp = Blueprint('players', __name__)


def _get_current_db_path():
    from app import get_current_db_path
    return get_current_db_path()


def _get_current_db():
    from app import get_current_db
    return get_current_db()


def _get_effective_player_ids(cursor, player_name):
    from app import get_effective_player_ids
    return get_effective_player_ids(cursor, player_name)


@players_bp.route('/api/players')
def get_players():
    """API endpoint to get all player names for autocomplete"""
    try:
        with sqlite3.connect(_get_current_db_path()) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # Get all effective player names with combined match counts
            # Show a player if they have ANY unmapped matches, plus all mapped player versions
            cursor.execute("""
                WITH all_players AS (
                    -- Players with at least one unmapped match
                    SELECT
                        p.name,
                        COUNT(DISTINCT smp.sub_match_id) as total_matches
                    FROM players p
                    JOIN sub_match_participants smp ON p.id = smp.player_id
                    JOIN sub_matches sm ON smp.sub_match_id = sm.id
                    JOIN matches m ON sm.match_id = m.id
                    WHERE smp.sub_match_id NOT IN (
                        SELECT DISTINCT sub_match_id
                        FROM sub_match_player_mappings
                        WHERE original_player_id = p.id
                    )
                    GROUP BY p.id, p.name

                    UNION ALL

                    -- Mapped player versions (from mappings table)
                    SELECT
                        smpm.correct_player_name as name,
                        COUNT(DISTINCT smpm.sub_match_id) as total_matches
                    FROM sub_match_player_mappings smpm
                    GROUP BY smpm.correct_player_name
                )
                SELECT
                    name,
                    SUM(total_matches) as combined_matches
                FROM all_players
                GROUP BY name
                HAVING SUM(total_matches) >= 1
                ORDER BY name
            """)

            players = [row['name'] for row in cursor.fetchall()]

            return jsonify(players)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@players_bp.route('/api/player/<player_name>')
def get_player_stats(player_name):
    """API endpoint to get detailed player statistics"""
    try:
        # URL decode the player name first
        from urllib.parse import unquote
        player_name = unquote(player_name)

        # Get parameters
        limit = request.args.get('limit', type=int)
        season = request.args.get('season')
        division = request.args.get('division')

        # Check if player name includes team disambiguation like "Name (Team)"
        # BUT don't split if it's one of our contextual players like "Johan (Rockhangers)"
        team_filter = None
        selected_team = None

        # Check if this is a contextual player (exists as exact name in database)
        is_contextual_player = False
        with sqlite3.connect(_get_current_db_path()) as temp_conn:
            temp_cursor = temp_conn.cursor()
            temp_cursor.execute("SELECT id FROM players WHERE name = ?", (player_name,))
            if temp_cursor.fetchone():
                is_contextual_player = True

        if '(' in player_name and player_name.endswith(')') and not is_contextual_player:
            # Extract team from player name like "Mats Andersson (SpikKastarna (SL6))"
            base_name = player_name.split(' (')[0]
            team_part = player_name.split(' (', 1)[1][:-1]  # Remove last )
            selected_team = team_part  # Store for display purposes
            player_name = base_name
            # Don't set team_filter - we want ALL matches for the player

        stats = _get_current_db().get_player_stats(player_name, season=season, division=division, team_filter=None)
        if not stats:
            return jsonify({'error': 'Player not found'}), 404

        # Apply limit if specified
        if limit and 'recent_matches' in stats:
            stats['recent_matches'] = stats['recent_matches'][:limit]

        # Convert datetime objects to strings for JSON serialization
        if 'recent_matches' in stats:
            for match in stats['recent_matches']:
                if 'match_date' in match and match['match_date']:
                    match['match_date'] = str(match['match_date'])

        # Add filter information to response
        stats['filters'] = {
            'season': season,
            'division': division,
            'team': None,  # No team filter applied
            'selected_team': selected_team  # Which team was selected (for display)
        }

        return jsonify(stats)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@players_bp.route('/api/player/<player_name>/detailed')
def get_player_detailed_stats(player_name):
    """Get detailed player statistics including match history and trends"""
    try:
        # URL decode the player name first
        from urllib.parse import unquote
        player_name = unquote(player_name)

        with sqlite3.connect(_get_current_db_path()) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # Get all effective player IDs (including mapped ones)
            all_player_ids = _get_effective_player_ids(cursor, player_name)
            if not all_player_ids:
                return jsonify({'error': 'Player not found'}), 404

            # Get detailed match history with averages over time
            cursor.execute("""
                SELECT
                    m.match_date,
                    t1.name as team1_name,
                    t2.name as team2_name,
                    CASE
                        WHEN sm.match_name LIKE '% AD' OR sm.match_name LIKE '% AD %' 
                             OR sm.match_name LIKE '%Dubbel%' OR sm.match_name LIKE '%Doubles%' THEN 'Doubles'
                        ELSE sm.match_type
                    END as match_type,
                    sm.match_name,
                    sm.team1_legs,
                    sm.team2_legs,
                    smp.team_number,
                    smp.player_avg,
                    CASE WHEN smp.team_number = 1 THEN t1.name ELSE t2.name END as player_team,
                    CASE
                        WHEN (smp.team_number = 1 AND sm.team1_legs > sm.team2_legs)
                          OR (smp.team_number = 2 AND sm.team2_legs > sm.team1_legs)
                        THEN 1 ELSE 0
                    END as won,
                    sm.id as sub_match_id
                FROM sub_match_participants smp
                JOIN sub_matches sm ON smp.sub_match_id = sm.id
                JOIN matches m ON sm.match_id = m.id
                JOIN teams t1 ON m.team1_id = t1.id
                JOIN teams t2 ON m.team2_id = t2.id
                WHERE smp.player_id IN ({})
                ORDER BY m.match_date DESC, sm.match_number
            """.format(','.join(['?' for _ in all_player_ids])), all_player_ids)

            matches = [dict(row) for row in cursor.fetchall()]

            # Get match type breakdown
            cursor.execute("""
                SELECT
                    sm.match_type,
                    COUNT(*) as total_matches,
                    SUM(CASE
                        WHEN (smp.team_number = 1 AND sm.team1_legs > sm.team2_legs)
                          OR (smp.team_number = 2 AND sm.team2_legs > sm.team1_legs)
                        THEN 1 ELSE 0
                    END) as wins,
                    AVG(smp.player_avg) as avg_score
                FROM sub_match_participants smp
                JOIN sub_matches sm ON smp.sub_match_id = sm.id
                WHERE smp.player_id IN ({})
                GROUP BY sm.match_type
            """.format(','.join(['?' for _ in all_player_ids])), all_player_ids)

            match_type_stats = [dict(row) for row in cursor.fetchall()]

            # Calculate trends (last 10 vs previous 10)
            recent_matches = matches[:10] if len(matches) >= 10 else matches
            previous_matches = matches[10:20] if len(matches) >= 20 else []

            recent_avg = sum(m['player_avg'] for m in recent_matches if m['player_avg']) / max(1, len([m for m in recent_matches if m['player_avg']]))
            previous_avg = sum(m['player_avg'] for m in previous_matches if m['player_avg']) / max(1, len([m for m in previous_matches if m['player_avg']])) if previous_matches else recent_avg

            # Convert dates for JSON
            for match in matches:
                if match['match_date']:
                    match['match_date'] = str(match['match_date'])

            return jsonify({
                'player_name': player_name,
                'match_history': matches,
                'match_type_breakdown': match_type_stats,
                'trends': {
                    'recent_average': round(recent_avg, 2),
                    'previous_average': round(previous_avg, 2),
                    'improvement': round(recent_avg - previous_avg, 2)
                }
            })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@players_bp.route('/player/<player_name>')
def player_detail(player_name):
    """Player detail page"""
    league = request.args.get('league', '')
    return render_template('player_detail.html', player_name=player_name, league=league)


@players_bp.route('/api/player/<player_name>/throws')
def get_player_throws(player_name):
    """Get detailed throw analysis for a player"""
    try:
        # URL decode the player name first
        from urllib.parse import unquote
        player_name = unquote(player_name)

        with sqlite3.connect(_get_current_db_path()) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # Get filter parameters
            season = request.args.get('season')
            division = request.args.get('division')

            # Check if player name includes team disambiguation like "Name (Team)"
            # BUT don't split if it's one of our contextual players like "Johan (Rockhangers)"
            original_player_name = player_name

            # Check if this is a contextual player (exists as exact name in database)
            is_contextual_player = False
            cursor.execute("SELECT id FROM players WHERE name = ?", (player_name,))
            if cursor.fetchone():
                is_contextual_player = True

            if '(' in player_name and player_name.endswith(')') and not is_contextual_player:
                # Extract team from player name like "Mats Andersson (SpikKastarna (SL6))"
                base_name = player_name.split(' (')[0]
                team_part = player_name.split(' (', 1)[1][:-1]  # Remove last )
                player_name = base_name
                # Don't use team filter - we want ALL throws for the player
                print(f"DEBUG: Original: '{original_player_name}' -> Base: '{player_name}', No team filter", flush=True)

            # Get player ID and build query with sub-match mappings
            player_ids = _get_effective_player_ids(cursor, player_name)

            if not player_ids:
                return jsonify({'error': 'Player not found'}), 404

            try:
                print(f"DEBUG: Found player ID for '{player_name}': {player_ids[0]}", flush=True)
            except (OSError, UnicodeEncodeError):
                print(f"DEBUG: Found player ID: {player_ids[0]}", flush=True)

            # Build WHERE clause that handles sub-match mappings correctly
            where_conditions = [
                """(
                    -- Include direct matches for this player, but exclude mapped-away sub-matches
                    (smp.player_id = ? AND p.name = ?
                     AND smp.sub_match_id NOT IN (
                         SELECT smpm.sub_match_id
                         FROM sub_match_player_mappings smpm
                         WHERE smpm.original_player_id = ?
                     )
                    )
                    OR
                    -- Include sub-matches that are mapped TO this player
                    (smp.sub_match_id IN (
                        SELECT smpm.sub_match_id
                        FROM sub_match_player_mappings smpm
                        WHERE smpm.correct_player_name = ?
                    ) AND smp.player_id IN (
                        SELECT DISTINCT smpm2.original_player_id
                        FROM sub_match_player_mappings smpm2
                        WHERE smpm2.correct_player_name = ?
                    ))
                ) AND (
                    CASE
                        WHEN sm.match_name LIKE '% AD' OR sm.match_name LIKE '% AD %' 
                             OR sm.match_name LIKE '%Dubbel%' OR sm.match_name LIKE '%Doubles%' THEN 'Doubles'
                        ELSE sm.match_type
                    END
                ) = 'Singles'"""
            ]
            params = [player_ids[0], player_name, player_ids[0], player_name, player_name]

            if season:
                where_conditions.append("m.season = ?")
                params.append(season)

            if division:
                where_conditions.append("m.division = ?")
                params.append(division)

            # No team filter - show throws from all teams

            where_clause = " AND ".join(where_conditions)

            # Get detailed throw data - ONLY from Singles matches with filtering
            cursor.execute(f"""
                SELECT
                    t.score,
                    t.remaining_score,
                    t.darts_used,
                    t.round_number,
                    l.leg_number,
                    sm.match_type,
                    sm.match_name,
                    m.match_date,
                    smp.player_avg,
                    CASE
                        WHEN (smp.team_number = 1 AND sm.team1_legs > sm.team2_legs)
                          OR (smp.team_number = 2 AND sm.team2_legs > sm.team1_legs)
                        THEN 1 ELSE 0
                    END as won_match
                FROM throws t
                JOIN legs l ON t.leg_id = l.id
                JOIN sub_matches sm ON l.sub_match_id = sm.id
                JOIN sub_match_participants smp ON sm.id = smp.sub_match_id
                JOIN players p ON smp.player_id = p.id
                JOIN matches m ON sm.match_id = m.id
                JOIN teams t1 ON m.team1_id = t1.id
                JOIN teams t2 ON m.team2_id = t2.id
                WHERE {where_clause}
                AND t.team_number = smp.team_number
                ORDER BY m.match_date DESC, l.leg_number, t.round_number
            """, params)

            throws = [dict(row) for row in cursor.fetchall()]

            # Calculate throw statistics
            if throws:
                # Remove duplicates by creating unique identifier for each throw
                unique_throws = {}
                for t in throws:
                    # Create unique key from match_date, leg_number, round_number, and score
                    key = f"{t['match_date']}_{t['leg_number']}_{t['round_number']}_{t['score']}"
                    if key not in unique_throws:
                        unique_throws[key] = t

                # Use deduplicated throws for calculations
                dedup_throws = list(unique_throws.values())
                scores = [t['score'] for t in dedup_throws if t['score'] > 0]  # For max and ranges

                # Calculate weighted average (same method as database.py)
                # Group throws by match to get player_avg and won/lost status
                unique_matches = {}
                for throw in dedup_throws:
                    match_key = f"{throw['match_date']}_{throw['match_name']}"
                    if match_key not in unique_matches and throw['player_avg'] is not None:
                        unique_matches[match_key] = {
                            'player_avg': throw['player_avg'],
                            'won': throw['won_match'] == 1,
                            'throws': []
                        }

                # Assign throws to matches
                for throw in dedup_throws:
                    match_key = f"{throw['match_date']}_{throw['match_name']}"
                    if match_key in unique_matches:
                        unique_matches[match_key]['throws'].append(throw)

                # Calculate weighted average for all matches
                total_score = 0.0
                total_darts = 0
                won_total_score = 0.0
                won_total_darts = 0
                lost_total_score = 0.0
                lost_total_darts = 0
                won_matches_count = 0
                lost_matches_count = 0

                for match_key, match_data in unique_matches.items():
                    player_avg = match_data['player_avg']
                    match_throws = match_data['throws']
                    won = match_data['won']

                    # Count darts for this match (using same logic as database.py)
                    match_darts = 0
                    for throw in match_throws:
                        score = throw['score']
                        remaining = throw['remaining_score']
                        darts_used = throw['darts_used']

                        # Skip starting throw (score=0, remaining=501)
                        if score == 0 and remaining == 501:
                            continue

                        if remaining == 0:
                            # Checkout - detect format based on score value
                            if score <= 3:
                                # Standard format: score = number of darts
                                checkout_darts = score if score else 3
                            else:
                                # Alternative format: score = points, use darts_used
                                checkout_darts = darts_used if darts_used else 3
                            match_darts += checkout_darts
                        else:
                            # Regular throw: always count darts
                            match_darts += (darts_used if darts_used else 3)

                    # Calculate score for this match
                    match_score = (player_avg * match_darts) / 3.0
                    total_score += match_score
                    total_darts += match_darts

                    if won:
                        won_total_score += match_score
                        won_total_darts += match_darts
                        won_matches_count += 1
                    else:
                        lost_total_score += match_score
                        lost_total_darts += match_darts
                        lost_matches_count += 1

                # Calculate final weighted averages
                avg_score = (total_score / total_darts * 3.0) if total_darts > 0 else 0
                avg_score_won = (won_total_score / won_total_darts * 3.0) if won_total_darts > 0 else 0
                avg_score_lost = (lost_total_score / lost_total_darts * 3.0) if lost_total_darts > 0 else 0
                max_score = max(scores) if scores else 0

                # Count different score ranges
                score_ranges = {
                    '26': len([s for s in scores if s == 26]),
                    '41-59': len([s for s in scores if 41 <= s <= 59]),
                    '60': len([s for s in scores if s == 60]),
                    '61-80': len([s for s in scores if 61 <= s <= 80]),
                    '81-99': len([s for s in scores if 81 <= s <= 99]),
                    '100': len([s for s in scores if s == 100]),
                    '101-139': len([s for s in scores if 101 <= s <= 139]),
                    '140+': len([s for s in scores if s >= 140])
                }

                # Calculate checkouts (scores when remaining_score became 0)
                checkouts = [t['score'] for t in dedup_throws if t['remaining_score'] == 0 and t['score'] > 0]

                # Advanced statistics
                throws_over_100 = len([s for s in scores if s >= 100])
                throws_180 = len([s for s in scores if s == 180])
                throws_over_140 = len([s for s in scores if s >= 140])
                throws_26 = len([s for s in scores if s == 26])
                throws_under_20 = len([s for s in scores if s < 20])

                # High finishes (checkouts 100+)
                # Group throws by leg to find the previous throw's remaining_score
                leg_throws_grouped = defaultdict(list)
                for t in dedup_throws:
                    leg_key = f"{t['match_date']}_{t['match_name']}_{t['leg_number']}"
                    leg_throws_grouped[leg_key].append(t)

                # Sort throws in each leg by round_number
                high_finishes = 0
                for leg_key, throws_in_leg in leg_throws_grouped.items():
                    throws_in_leg.sort(key=lambda x: x['round_number'])
                    for i, t in enumerate(throws_in_leg):
                        if t['remaining_score'] == 0:  # This is a checkout
                            # Get the previous throw's remaining_score (that's the checkout value)
                            if i > 0:
                                checkout_value = throws_in_leg[i-1]['remaining_score']
                                if checkout_value >= 100:
                                    high_finishes += 1

                # Short sets (legs won in 18 darts or fewer)
                # Count legs where player won and used <= 18 darts
                leg_darts = defaultdict(int)
                leg_winners = {}

                for throw in dedup_throws:
                    leg_id = f"{throw['match_date']}_{throw['match_name']}_{throw['leg_number']}"
                    leg_darts[leg_id] += throw['darts_used'] or 3

                    # If this is a finishing throw (remaining_score becomes 0), mark as won
                    if throw['remaining_score'] == 0:
                        leg_winners[leg_id] = True

                # Count legs won in 18 darts or fewer
                short_sets = sum(1 for leg_id in leg_winners.keys() if leg_darts[leg_id] <= 18)

                # Most common scores
                score_frequency = Counter(scores)
                most_common_scores = score_frequency.most_common(5)

                statistics = {
                    'total_throws': len(dedup_throws),
                    'average_score': round(avg_score, 2),
                    'average_score_won': round(avg_score_won, 2),
                    'average_score_lost': round(avg_score_lost, 2),
                    'won_matches_count': won_matches_count,
                    'lost_matches_count': lost_matches_count,
                    'max_score': max_score,
                    'score_ranges': score_ranges,
                    'total_checkouts': len(checkouts),
                    'checkout_scores': checkouts,
                    'throws_over_100': throws_over_100,
                    'throws_180': throws_180,
                    'throws_over_140': throws_over_140,
                    'throws_26': throws_26,
                    'throws_under_20': throws_under_20,
                    'high_finishes': high_finishes,
                    'short_sets': short_sets,
                    'most_common_scores': [{'score': score, 'count': count} for score, count in most_common_scores]
                }
                print(f"DEBUG: Total throws for '{original_player_name}': {len(dedup_throws)} (deduplicated from {len(throws)}), No team filter", flush=True)
            else:
                statistics = {}

            # Convert dates for JSON
            for throw in throws:
                if throw['match_date']:
                    throw['match_date'] = str(throw['match_date'])

            # Calculate ALL-TIME statistics (without season/division filters)
            all_time_statistics = {}
            if season or division:  # Only calculate if we have filters applied
                # Build WHERE clause without season/division filters
                all_time_where_conditions = [
                    """(
                        -- Include direct matches for this player, but exclude mapped-away sub-matches
                        (smp.player_id = ? AND p.name = ?
                         AND smp.sub_match_id NOT IN (
                             SELECT smpm.sub_match_id
                             FROM sub_match_player_mappings smpm
                             WHERE smpm.original_player_id = ?
                         )
                        )
                        OR
                        -- Include sub-matches that are mapped TO this player
                        (smp.sub_match_id IN (
                            SELECT smpm.sub_match_id
                            FROM sub_match_player_mappings smpm
                            WHERE smpm.correct_player_name = ?
                        ) AND smp.player_id IN (
                            SELECT DISTINCT smpm2.original_player_id
                            FROM sub_match_player_mappings smpm2
                            WHERE smpm2.correct_player_name = ?
                        ))
                    ) AND (
                        CASE
                            WHEN sm.match_name LIKE '% AD' OR sm.match_name LIKE '% AD %' 
                                 OR sm.match_name LIKE '%Dubbel%' OR sm.match_name LIKE '%Doubles%' THEN 'Doubles'
                            ELSE sm.match_type
                        END
                    ) = 'Singles'"""
                ]
                all_time_params = [player_ids[0], player_name, player_ids[0], player_name, player_name]
                all_time_where_clause = " AND ".join(all_time_where_conditions)

                # Get ALL throw data (no season/division filter)
                cursor.execute(f"""
                    SELECT
                        t.score,
                        t.remaining_score,
                        t.darts_used,
                        t.round_number,
                        l.leg_number,
                        sm.match_type,
                        sm.match_name,
                        m.match_date,
                        smp.player_avg,
                        CASE
                            WHEN (smp.team_number = 1 AND sm.team1_legs > sm.team2_legs)
                              OR (smp.team_number = 2 AND sm.team2_legs > sm.team1_legs)
                            THEN 1 ELSE 0
                        END as won_match
                    FROM throws t
                    JOIN legs l ON t.leg_id = l.id
                    JOIN sub_matches sm ON l.sub_match_id = sm.id
                    JOIN sub_match_participants smp ON sm.id = smp.sub_match_id
                    JOIN players p ON smp.player_id = p.id
                    JOIN matches m ON sm.match_id = m.id
                    JOIN teams t1 ON m.team1_id = t1.id
                    JOIN teams t2 ON m.team2_id = t2.id
                    WHERE {all_time_where_clause}
                    AND t.team_number = smp.team_number
                    ORDER BY m.match_date DESC, l.leg_number, t.round_number
                """, all_time_params)

                all_time_throws = [dict(row) for row in cursor.fetchall()]

                if all_time_throws:
                    # Deduplicate
                    unique_all_time = {}
                    for t in all_time_throws:
                        key = f"{t['match_date']}_{t['leg_number']}_{t['round_number']}_{t['score']}"
                        if key not in unique_all_time:
                            unique_all_time[key] = t

                    dedup_all_time = list(unique_all_time.values())
                    all_time_scores = [t['score'] for t in dedup_all_time if t['score'] > 0]

                    # Calculate statistics
                    all_time_throws_over_100 = len([s for s in all_time_scores if s >= 100])
                    all_time_throws_180 = len([s for s in all_time_scores if s == 180])
                    all_time_throws_over_140 = len([s for s in all_time_scores if s >= 140])

                    # High finishes - group by leg and check previous throw's remaining_score
                    all_time_leg_throws = defaultdict(list)
                    for t in dedup_all_time:
                        leg_key = f"{t['match_date']}_{t['match_name']}_{t['leg_number']}"
                        all_time_leg_throws[leg_key].append(t)

                    all_time_high_finishes = 0
                    for leg_key, throws_in_leg in all_time_leg_throws.items():
                        throws_in_leg.sort(key=lambda x: x['round_number'])
                        for i, t in enumerate(throws_in_leg):
                            if t['remaining_score'] == 0 and i > 0:
                                checkout_value = throws_in_leg[i-1]['remaining_score']
                                if checkout_value >= 100:
                                    all_time_high_finishes += 1

                    all_time_score_ranges = {
                        '26': len([s for s in all_time_scores if s == 26]),
                        '41-59': len([s for s in all_time_scores if 41 <= s <= 59]),
                        '60': len([s for s in all_time_scores if s == 60]),
                        '61-80': len([s for s in all_time_scores if 61 <= s <= 80]),
                        '81-99': len([s for s in all_time_scores if 81 <= s <= 99]),
                        '100': len([s for s in all_time_scores if s == 100]),
                        '101-139': len([s for s in all_time_scores if 101 <= s <= 139]),
                        '140+': len([s for s in all_time_scores if s >= 140])
                    }

                    all_time_statistics = {
                        'throws_over_100': all_time_throws_over_100,
                        'throws_over_140': all_time_throws_over_140,
                        'throws_180': all_time_throws_180,
                        'high_finishes': all_time_high_finishes,
                        'score_ranges': all_time_score_ranges
                    }
            else:
                # No filters applied, use current statistics as all-time
                all_time_statistics = {
                    'throws_over_100': statistics.get('throws_over_100', 0),
                    'throws_over_140': statistics.get('throws_over_140', 0),
                    'throws_180': statistics.get('throws_180', 0),
                    'high_finishes': statistics.get('high_finishes', 0),
                    'score_ranges': statistics.get('score_ranges', {})
                } if statistics else {}

            return jsonify({
                'player_name': player_name,
                'throws': throws[:100],  # Limit to last 100 throws for performance
                'statistics': statistics,
                'all_time_statistics': all_time_statistics
            })

    except Exception as e:
        import traceback
        try:
            print(f"ERROR in get_player_throws for '{player_name}': {str(e)}", flush=True)
        except (OSError, UnicodeEncodeError):
            print(f"ERROR in get_player_throws: {str(e)}", flush=True)
        print(f"Full traceback: {traceback.format_exc()}", flush=True)
        return jsonify({'error': str(e)}), 500


@players_bp.route('/api/player/<int:player_id>/memorable-matches')
def get_memorable_matches(player_id):
    """Hamta de tre mest minnesvarda matcherna for en spelare baserat pa pilsnitt, korta set och hoga utgangar"""
    try:
        with sqlite3.connect(_get_current_db_path()) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # Hamta alla singelmatcher for spelaren med detaljerad statistik
            cursor.execute("""
                SELECT DISTINCT
                    sm.id as sub_match_id,
                    sm.match_id,
                    m.match_date as date,
                    m.season,
                    m.division,
                    home_team.name as home_team,
                    away_team.name as away_team,
                    smp.team_number,
                    sm.team1_legs,
                    sm.team2_legs,
                    CASE
                        WHEN smp.team_number = 1 THEN away_team.name
                        ELSE home_team.name
                    END as opponent_team,
                    CASE
                        WHEN (smp.team_number = 1 AND sm.team1_legs > sm.team2_legs)
                          OR (smp.team_number = 2 AND sm.team2_legs > sm.team1_legs) THEN 1
                        ELSE 0
                    END as won_match
                FROM sub_matches sm
                JOIN sub_match_participants smp ON sm.id = smp.sub_match_id
                JOIN matches m ON sm.match_id = m.id
                JOIN teams home_team ON m.team1_id = home_team.id
                JOIN teams away_team ON m.team2_id = away_team.id
                WHERE smp.player_id = ? AND (
                    CASE
                        WHEN sm.match_name LIKE '% AD' OR sm.match_name LIKE '% AD %' 
                             OR sm.match_name LIKE '%Dubbel%' OR sm.match_name LIKE '%Doubles%' THEN 'Doubles'
                        ELSE sm.match_type
                    END
                ) = 'Singles'
                ORDER BY m.match_date DESC
            """, (player_id,))

            matches = cursor.fetchall()
            memorable_matches = []

            for match in matches:
                sub_match_id = match['sub_match_id']

                # Hamta kastdata for denna match
                cursor.execute("""
                    SELECT DISTINCT
                        t.score,
                        t.remaining_score,
                        t.leg_id,
                        t.round_number
                    FROM throws t
                    JOIN legs l ON t.leg_id = l.id
                    JOIN sub_match_participants smp ON l.sub_match_id = smp.sub_match_id
                    WHERE l.sub_match_id = ? AND smp.player_id = ? AND t.team_number = smp.team_number
                    ORDER BY t.leg_id, t.round_number
                """, (sub_match_id, player_id))

                throws = cursor.fetchall()

                if not throws:
                    continue

                # Berakna statistik for denna match
                total_score = sum(t['score'] for t in throws)
                total_throws = len(throws)
                average_score = total_score / total_throws if total_throws > 0 else 0

                # Rakna hoga utgangar (100+) - kolla foregaende kasts remaining_score
                leg_throws_for_checkout = {}
                for t in throws:
                    leg_id = t['leg_id']
                    if leg_id not in leg_throws_for_checkout:
                        leg_throws_for_checkout[leg_id] = []
                    leg_throws_for_checkout[leg_id].append(t)

                high_finishes = 0
                for leg_id, leg_throws_list in leg_throws_for_checkout.items():
                    leg_throws_list.sort(key=lambda x: x['round_number'])
                    for i, t in enumerate(leg_throws_list):
                        if t['remaining_score'] == 0 and i > 0:
                            checkout_value = leg_throws_list[i-1]['remaining_score']
                            if checkout_value >= 100:
                                high_finishes += 1

                # Rakna korta set (<=18 kast per leg)
                leg_throws = {}
                for throw in throws:
                    leg_id = throw['leg_id']
                    if leg_id not in leg_throws:
                        leg_throws[leg_id] = 0
                    leg_throws[leg_id] += 1

                short_sets = sum(1 for count in leg_throws.values() if count <= 18)

                # Berakna "minnesvardhet" - kombinera pilsnitt, korta set och hoga utgangar
                # Normalisera vardena och ge dem vikter
                memorability_score = (
                    (average_score / 50.0) * 0.4 +  # Pilsnitt (normaliserat mot 50)
                    (short_sets * 2.0) * 0.3 +       # Korta set (2 poang per kort set)
                    (high_finishes * 3.0) * 0.3      # Hoga utgangar (3 poang per hog utgang)
                )

                memorable_matches.append({
                    'sub_match_id': sub_match_id,
                    'match_id': match['match_id'],
                    'date': match['date'],
                    'season': match['season'],
                    'division': match['division'],
                    'home_team': match['home_team'],
                    'away_team': match['away_team'],
                    'opponent_team': match['opponent_team'],
                    'won_match': bool(match['won_match']),
                    'average_score': round(average_score, 2),
                    'high_finishes': high_finishes,
                    'short_sets': short_sets,
                    'memorability_score': round(memorability_score, 2),
                    'total_throws': total_throws
                })

            # Sortera efter minnesvardhet och ta de tre basta
            memorable_matches.sort(key=lambda x: x['memorability_score'], reverse=True)
            top_3_matches = memorable_matches[:3]

            return jsonify({
                'memorable_matches': top_3_matches
            })

    except Exception as e:
        return jsonify({'error': str(e)}), 500
