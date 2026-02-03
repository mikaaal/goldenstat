import sqlite3
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify, render_template

league_bp = Blueprint('league', __name__)


def _get_current_db_path():
    from app import get_current_db_path
    return get_current_db_path()


def _get_cache_backend():
    """Get the underlying cache backend via current_app to avoid reloader identity issues"""
    from flask import current_app
    cache_ext = current_app.extensions.get('cache', {})
    # Get the first (and typically only) cache backend
    for backend in cache_ext.values():
        return backend
    return None


@league_bp.route('/')
def index():
    """Main page with player search"""
    league = request.args.get('league', '')
    tab = request.args.get('tab', 'players')
    return render_template('index.html', league=league, tab=tab)


@league_bp.route('/api/last-import')
def get_last_import():
    """API endpoint to get last import info"""
    try:
        import os
        import json
        import glob

        log_dir = 'import_logs'
        league = request.args.get('league', '')
        if league == 'riksserien':
            files = glob.glob(os.path.join(log_dir, 'riksserien_daily_import_*.json'))
        else:
            files = glob.glob(os.path.join(log_dir, 'daily_import_*.json'))

        if not files:
            return jsonify({'error': 'No import logs found'}), 404

        # Sort by filename (which contains timestamp) instead of file modification time
        # This is important in Docker where all files get the same mtime during build
        latest_file = max(files)

        with open(latest_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        end_time = datetime.fromisoformat(data['end_time'])

        return jsonify({
            'import_id': data['import_id'],
            'status': data['status'],
            'end_time': end_time.strftime('%Y-%m-%d %H:%M'),
            'total_matches': data['statistics']['total_matches_imported'],
            'total_files': data['statistics']['total_files']
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@league_bp.route('/api/divisions')
def get_divisions():
    """API endpoint to get all divisions for current season"""
    try:
        with sqlite3.connect(_get_current_db_path()) as conn:
            cursor = conn.cursor()

            # Get current season (most recent)
            cursor.execute("""
                SELECT season
                FROM matches
                WHERE season IS NOT NULL
                ORDER BY match_date DESC
                LIMIT 1
            """)
            current_season_row = cursor.fetchone()

            if not current_season_row:
                return jsonify([])

            current_season = current_season_row[0]

            # Get divisions for current season
            cursor.execute("""
                SELECT DISTINCT division
                FROM matches
                WHERE division IS NOT NULL
                  AND season = ?
            """, (current_season,))
            divisions = []
            for row in cursor.fetchall():
                div = row[0]
                # Fix division names for display
                if div == "Mixed":
                    # Get a sample match to determine X1 or X2
                    cursor.execute("""
                        SELECT t1.name FROM matches m
                        JOIN teams t1 ON m.team1_id = t1.id
                        WHERE m.division = ? AND m.season = ?
                        LIMIT 1
                    """, (div, current_season))
                    team_row = cursor.fetchone()
                    if team_row and "(X1)" in team_row[0]:
                        divisions.append("Mixed (X1)")
                    else:
                        divisions.append(div)
                elif div == "Mixed(":
                    # This is X2
                    divisions.append("Mixed (X2)")
                elif div == "Superligan":
                    # Display as SL6 to match team names
                    divisions.append("SL6")
                else:
                    divisions.append(div)

            # Custom sort per league
            league = request.args.get('league', '')
            if league == 'riksserien':
                # Riksserien: Elit, Elit Dam, Superettan, Superettan Dam, then Div descending
                rs_priority = {
                    'Elit': 0, 'Elit Dam': 1,
                    'Superettan': 2, 'Superettan Dam': 3,
                }
                top_divs = sorted([d for d in divisions if d in rs_priority], key=lambda d: rs_priority[d])
                rest_divs = sorted([d for d in divisions if d not in rs_priority])
                return jsonify(top_divs + rest_divs)
            else:
                # Stockholmsserien: SL6 first, then SL4, then rest ascending, Mixed last
                sl_divisions = [d for d in divisions if d in ["SL6", "SL4"]]
                mixed_divisions = [d for d in divisions if "Mixed" in d]
                other_divisions = [d for d in divisions if d not in ["SL6", "SL4"] and "Mixed" not in d]
                other_divisions.sort()
                return jsonify(sl_divisions + other_divisions + mixed_divisions)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@league_bp.route('/api/leagues')
def get_leagues():
    """Get available leagues and seasons"""
    try:
        with sqlite3.connect(_get_current_db_path()) as conn:
            cursor = conn.cursor()

            # Get distinct seasons and divisions
            cursor.execute("""
                SELECT DISTINCT season, division
                FROM matches
                WHERE season IS NOT NULL OR division IS NOT NULL
                ORDER BY season DESC, division ASC
            """)

            leagues = []
            seasons = set()
            divisions = set()

            for row in cursor.fetchall():
                season = row[0] or 'Unknown'
                division = row[1] or 'Unknown'
                leagues.append({'season': season, 'division': division})
                seasons.add(season)
                divisions.add(division)

            return jsonify({
                'leagues': leagues,
                'seasons': sorted(list(seasons), reverse=True),
                'divisions': sorted(list(divisions))
            })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@league_bp.route('/api/overview')
def get_overview():
    """Get database overview statistics"""
    try:
        with sqlite3.connect(_get_current_db_path()) as conn:
            cursor = conn.cursor()

            # Get query parameters for filtering
            season = request.args.get('season')
            division = request.args.get('division')

            # Build WHERE clause for filtering
            where_conditions = []
            params = []

            if season:
                where_conditions.append("m.season = ?")
                params.append(season)

            if division:
                where_conditions.append("m.division = ?")
                params.append(division)

            where_clause = " AND ".join(where_conditions)
            if where_clause:
                where_clause = " WHERE " + where_clause

            # Get basic counts with filtering
            cursor.execute(f"SELECT COUNT(DISTINCT p.id) FROM players p JOIN sub_match_participants smp ON p.id = smp.player_id JOIN sub_matches sm ON smp.sub_match_id = sm.id JOIN matches m ON sm.match_id = m.id{where_clause}", params)
            total_players = cursor.fetchone()[0]

            cursor.execute(f"SELECT COUNT(*) FROM matches m{where_clause}", params)
            total_matches = cursor.fetchone()[0]

            cursor.execute(f"SELECT COUNT(*) FROM sub_matches sm JOIN matches m ON sm.match_id = m.id{where_clause}", params)
            total_sub_matches = cursor.fetchone()[0]

            cursor.execute(f"SELECT COUNT(*) FROM legs l JOIN sub_matches sm ON l.sub_match_id = sm.id JOIN matches m ON sm.match_id = m.id{where_clause}", params)
            total_legs = cursor.fetchone()[0]

            cursor.execute(f"SELECT COUNT(*) FROM throws t JOIN legs l ON t.leg_id = l.id JOIN sub_matches sm ON l.sub_match_id = sm.id JOIN matches m ON sm.match_id = m.id{where_clause}", params)
            total_throws = cursor.fetchone()[0]

            # Get recent activity with filtering
            cursor.execute(f"""
                SELECT
                    t1.name as team1, t2.name as team2,
                    m.team1_score, m.team2_score,
                    m.scraped_at, m.season, m.division
                FROM matches m
                JOIN teams t1 ON m.team1_id = t1.id
                JOIN teams t2 ON m.team2_id = t2.id
                {where_clause}
                ORDER BY m.scraped_at DESC
                LIMIT 5
            """, params)

            recent_matches = []
            for row in cursor.fetchall():
                recent_matches.append({
                    'team1': row[0],
                    'team2': row[1],
                    'team1_score': row[2],
                    'team2_score': row[3],
                    'scraped_at': str(row[4]),
                    'season': row[5],
                    'division': row[6]
                })

            return jsonify({
                'total_players': total_players,
                'total_matches': total_matches,
                'total_sub_matches': total_sub_matches,
                'total_legs': total_legs,
                'total_throws': total_throws,
                'recent_matches': recent_matches,
                'filters': {
                    'season': season,
                    'division': division
                }
            })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@league_bp.route('/api/top-stats')
def get_top_stats():
    """API endpoint to get top statistics"""
    cache_backend = _get_cache_backend()
    cache_key = f"top_stats_{request.query_string.decode()}"
    if cache_backend:
        cached = cache_backend.get(cache_key)
        if cached is not None:
            return cached

    try:
        with sqlite3.connect(_get_current_db_path()) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # Get optional season filter from query parameter
            season = request.args.get('season')
            season_filter = ""
            if season:
                season_filter = f"AND m.season = '{season}'"

            # Top 10 highest averages in a single match (Singles only)
            cursor.execute(f"""
                SELECT
                    p.name as player_name,
                    smp.player_avg as average,
                    smp.team_number as team_number,
                    CASE WHEN smp.team_number = 1 THEN t1.name ELSE t2.name END as team_name,
                    CASE WHEN smp.team_number = 1 THEN t2.name ELSE t1.name END as opponent_name,
                    DATE(m.match_date) as match_date,
                    sm.id as sub_match_id
                FROM sub_match_participants smp
                JOIN players p ON smp.player_id = p.id
                JOIN sub_matches sm ON smp.sub_match_id = sm.id
                JOIN matches m ON sm.match_id = m.id
                JOIN teams t1 ON m.team1_id = t1.id
                JOIN teams t2 ON m.team2_id = t2.id
                WHERE sm.match_type = 'Singles'
                    AND smp.player_avg > 0
                {season_filter}
                ORDER BY smp.player_avg DESC
                LIMIT 10
            """)
            top_averages = [dict(row) for row in cursor.fetchall()]

            # Top 10 highest checkouts
            cursor.execute(f"""
                SELECT
                    p.name as player_name,
                    prev.remaining_score as checkout,
                    curr.team_number as team_number,
                    CASE WHEN curr.team_number = 1 THEN t1.name ELSE t2.name END as team_name,
                    CASE WHEN curr.team_number = 1 THEN t2.name ELSE t1.name END as opponent_name,
                    DATE(m.match_date) as match_date,
                    sm.id as sub_match_id
                FROM throws curr
                JOIN throws prev ON curr.leg_id = prev.leg_id
                    AND curr.team_number = prev.team_number
                    AND prev.round_number = curr.round_number - 1
                JOIN legs l ON curr.leg_id = l.id
                JOIN sub_matches sm ON l.sub_match_id = sm.id
                JOIN sub_match_participants smp ON sm.id = smp.sub_match_id AND smp.team_number = curr.team_number
                JOIN players p ON smp.player_id = p.id
                JOIN matches m ON sm.match_id = m.id
                JOIN teams t1 ON m.team1_id = t1.id
                JOIN teams t2 ON m.team2_id = t2.id
                WHERE curr.remaining_score = 0
                    AND prev.remaining_score > 0
                    AND curr.team_number = l.winner_team
                    AND sm.match_type = 'Singles'
                    {season_filter}
                ORDER BY prev.remaining_score DESC, m.match_date DESC
                LIMIT 10
            """)
            top_checkouts = [dict(row) for row in cursor.fetchall()]

            # Top 10 shortest legs (minimum darts)
            cursor.execute(f"""
                WITH completed_legs AS (
                    SELECT DISTINCT l.id
                    FROM legs l
                    JOIN throws t ON l.id = t.leg_id
                    WHERE t.remaining_score = 0
                ),
                leg_darts AS (
                    SELECT
                        l.id as leg_id,
                        l.winner_team,
                        sm.id as sub_match_id,
                        SUM(CASE WHEN t.darts_used IS NOT NULL THEN t.darts_used ELSE 3 END) as total_darts
                    FROM legs l
                    JOIN completed_legs cl ON l.id = cl.id
                    JOIN throws t ON l.id = t.leg_id AND t.team_number = l.winner_team
                    JOIN sub_matches sm ON l.sub_match_id = sm.id
                    WHERE NOT (t.score = 0 AND t.remaining_score = 501)
                    GROUP BY l.id, l.winner_team, sm.id
                )
                SELECT
                    p.name as player_name,
                    ld.total_darts as darts,
                    smp.team_number as team_number,
                    t1.name as team_name,
                    t2.name as opponent_name,
                    DATE(m.match_date) as match_date,
                    ld.sub_match_id
                FROM leg_darts ld
                JOIN sub_matches sm ON ld.sub_match_id = sm.id
                JOIN sub_match_participants smp ON sm.id = smp.sub_match_id AND smp.team_number = ld.winner_team
                JOIN players p ON smp.player_id = p.id
                JOIN matches m ON sm.match_id = m.id
                JOIN teams t1 ON (CASE WHEN smp.team_number = 1 THEN m.team1_id ELSE m.team2_id END) = t1.id
                JOIN teams t2 ON (CASE WHEN smp.team_number = 1 THEN m.team2_id ELSE m.team1_id END) = t2.id
                WHERE ld.total_darts > 0
                    AND sm.match_type = 'Singles'
                    {season_filter}
                ORDER BY ld.total_darts ASC, m.match_date DESC
                LIMIT 10
            """)
            shortest_sets = [dict(row) for row in cursor.fetchall()]

            # Top 10 most 180s in a single match
            cursor.execute(f"""
                WITH match_180s AS (
                    SELECT
                        sm.id as sub_match_id,
                        t.team_number,
                        COUNT(*) as count_180
                    FROM throws t
                    JOIN legs l ON t.leg_id = l.id
                    JOIN sub_matches sm ON l.sub_match_id = sm.id
                    WHERE t.score = 180
                    GROUP BY sm.id, t.team_number
                )
                SELECT
                    p.name as player_name,
                    m180.count_180,
                    smp.team_number as team_number,
                    t1.name as team_name,
                    t2.name as opponent_name,
                    DATE(m.match_date) as match_date,
                    sm.id as sub_match_id
                FROM match_180s m180
                JOIN sub_matches sm ON m180.sub_match_id = sm.id
                JOIN sub_match_participants smp ON sm.id = smp.sub_match_id AND smp.team_number = m180.team_number
                JOIN players p ON smp.player_id = p.id
                JOIN matches m ON sm.match_id = m.id
                JOIN teams t1 ON (CASE WHEN smp.team_number = 1 THEN m.team1_id ELSE m.team2_id END) = t1.id
                JOIN teams t2 ON (CASE WHEN smp.team_number = 1 THEN m.team2_id ELSE m.team1_id END) = t2.id
                WHERE sm.match_type = 'Singles'
                {season_filter}
                ORDER BY m180.count_180 DESC, m.match_date DESC
                LIMIT 10
            """)
            most_180s = [dict(row) for row in cursor.fetchall()]

            result = jsonify({
                'top_averages': top_averages,
                'top_checkouts': top_checkouts,
                'shortest_sets': shortest_sets,
                'most_180s': most_180s
            })

            if cache_backend:
                cache_backend.set(cache_key, result)
            return result

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@league_bp.route('/api/weekly-stats')
def get_weekly_stats():
    """API endpoint to get statistics for the current week"""
    cache_backend = _get_cache_backend()
    cache_key = f"weekly_stats_{request.query_string.decode()}"
    if cache_backend:
        cached = cache_backend.get(cache_key)
        if cached is not None:
            return cached

    try:
        with sqlite3.connect(_get_current_db_path()) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # Get optional division filter from query parameter
            division = request.args.get('division')

            # Support explicit date range (used by riksserien rounds)
            date_start = request.args.get('date_start')
            date_end = request.args.get('date_end')

            if date_start and date_end:
                start_of_week = datetime.strptime(date_start, '%Y-%m-%d')
                end_of_week = datetime.strptime(date_end, '%Y-%m-%d').replace(hour=23, minute=59, second=59)
                week_offset = 0
            else:
                # Get optional week_offset parameter (0 = current week, -1 = last week, etc.)
                week_offset = int(request.args.get('week_offset', 0))

                # Calculate week's date range (Monday to Sunday)
                today = datetime.now()
                # Get the start of the current week (Monday)
                start_of_week = today - timedelta(days=today.weekday())
                start_of_week = start_of_week.replace(hour=0, minute=0, second=0, microsecond=0)
                # Apply week offset
                start_of_week = start_of_week + timedelta(weeks=week_offset)
                # Get the end of the week (Sunday)
                end_of_week = start_of_week + timedelta(days=6, hours=23, minutes=59, seconds=59)

            # Build filter for SQL
            week_filter = f"AND m.match_date >= '{start_of_week.strftime('%Y-%m-%d %H:%M:%S')}' AND m.match_date <= '{end_of_week.strftime('%Y-%m-%d %H:%M:%S')}'"

            if division:
                week_filter += f" AND m.division = '{division}'"

            # Top 10 highest averages this week
            cursor.execute(f"""
                SELECT
                    p.name as player_name,
                    smp.player_avg as average,
                    smp.team_number as team_number,
                    CASE WHEN smp.team_number = 1 THEN t1.name ELSE t2.name END as team_name,
                    CASE WHEN smp.team_number = 1 THEN t2.name ELSE t1.name END as opponent_name,
                    DATE(m.match_date) as match_date,
                    sm.id as sub_match_id
                FROM sub_match_participants smp
                JOIN players p ON smp.player_id = p.id
                JOIN sub_matches sm ON smp.sub_match_id = sm.id
                JOIN matches m ON sm.match_id = m.id
                JOIN teams t1 ON m.team1_id = t1.id
                JOIN teams t2 ON m.team2_id = t2.id
                WHERE sm.match_type = 'Singles'
                    AND smp.player_avg > 0
                {week_filter}
                ORDER BY smp.player_avg DESC
                LIMIT 10
            """)
            top_averages = [dict(row) for row in cursor.fetchall()]

            # Top 10 highest checkouts this week
            cursor.execute(f"""
                SELECT
                    p.name as player_name,
                    prev.remaining_score as checkout,
                    curr.team_number as team_number,
                    CASE WHEN curr.team_number = 1 THEN t1.name ELSE t2.name END as team_name,
                    CASE WHEN curr.team_number = 1 THEN t2.name ELSE t1.name END as opponent_name,
                    DATE(m.match_date) as match_date,
                    sm.id as sub_match_id
                FROM throws curr
                JOIN throws prev ON curr.leg_id = prev.leg_id
                    AND curr.team_number = prev.team_number
                    AND prev.round_number = curr.round_number - 1
                JOIN legs l ON curr.leg_id = l.id
                JOIN sub_matches sm ON l.sub_match_id = sm.id
                JOIN sub_match_participants smp ON sm.id = smp.sub_match_id AND smp.team_number = curr.team_number
                JOIN players p ON smp.player_id = p.id
                JOIN matches m ON sm.match_id = m.id
                JOIN teams t1 ON m.team1_id = t1.id
                JOIN teams t2 ON m.team2_id = t2.id
                WHERE curr.remaining_score = 0
                    AND prev.remaining_score > 0
                    AND curr.team_number = l.winner_team
                    AND sm.match_type = 'Singles'
                {week_filter}
                ORDER BY prev.remaining_score DESC, m.match_date DESC
                LIMIT 10
            """)
            top_checkouts = [dict(row) for row in cursor.fetchall()]

            # Top 10 shortest legs this week
            cursor.execute(f"""
                WITH completed_legs AS (
                    SELECT DISTINCT l.id
                    FROM legs l
                    JOIN throws t ON l.id = t.leg_id
                    WHERE t.remaining_score = 0
                ),
                leg_darts AS (
                    SELECT
                        l.id as leg_id,
                        l.winner_team,
                        sm.id as sub_match_id,
                        SUM(CASE WHEN t.darts_used IS NOT NULL THEN t.darts_used ELSE 3 END) as total_darts
                    FROM legs l
                    JOIN completed_legs cl ON l.id = cl.id
                    JOIN throws t ON l.id = t.leg_id AND t.team_number = l.winner_team
                    JOIN sub_matches sm ON l.sub_match_id = sm.id
                    WHERE NOT (t.score = 0 AND t.remaining_score = 501)
                    GROUP BY l.id, l.winner_team, sm.id
                )
                SELECT
                    p.name as player_name,
                    ld.total_darts as darts,
                    smp.team_number as team_number,
                    t1.name as team_name,
                    t2.name as opponent_name,
                    DATE(m.match_date) as match_date,
                    ld.sub_match_id
                FROM leg_darts ld
                JOIN sub_matches sm ON ld.sub_match_id = sm.id
                JOIN sub_match_participants smp ON sm.id = smp.sub_match_id AND smp.team_number = ld.winner_team
                JOIN players p ON smp.player_id = p.id
                JOIN matches m ON sm.match_id = m.id
                JOIN teams t1 ON (CASE WHEN smp.team_number = 1 THEN m.team1_id ELSE m.team2_id END) = t1.id
                JOIN teams t2 ON (CASE WHEN smp.team_number = 1 THEN m.team2_id ELSE m.team1_id END) = t2.id
                WHERE ld.total_darts > 0
                    AND sm.match_type = 'Singles'
                {week_filter}
                ORDER BY ld.total_darts ASC, m.match_date DESC
                LIMIT 10
            """)
            shortest_sets = [dict(row) for row in cursor.fetchall()]

            # Top 10 most 100+ throws in a single match this week
            cursor.execute(f"""
                WITH match_100plus AS (
                    SELECT
                        sm.id as sub_match_id,
                        t.team_number,
                        COUNT(*) as count_100plus
                    FROM throws t
                    JOIN legs l ON t.leg_id = l.id
                    JOIN sub_matches sm ON l.sub_match_id = sm.id
                    WHERE t.score >= 100
                    GROUP BY sm.id, t.team_number
                )
                SELECT
                    p.name as player_name,
                    m100.count_100plus,
                    smp.team_number as team_number,
                    t1.name as team_name,
                    t2.name as opponent_name,
                    DATE(m.match_date) as match_date,
                    sm.id as sub_match_id
                FROM match_100plus m100
                JOIN sub_matches sm ON m100.sub_match_id = sm.id
                JOIN sub_match_participants smp ON sm.id = smp.sub_match_id AND smp.team_number = m100.team_number
                JOIN players p ON smp.player_id = p.id
                JOIN matches m ON sm.match_id = m.id
                JOIN teams t1 ON (CASE WHEN smp.team_number = 1 THEN m.team1_id ELSE m.team2_id END) = t1.id
                JOIN teams t2 ON (CASE WHEN smp.team_number = 1 THEN m.team2_id ELSE m.team1_id END) = t2.id
                WHERE sm.match_type = 'Singles'
                {week_filter}
                ORDER BY m100.count_100plus DESC, m.match_date DESC
                LIMIT 10
            """)
            most_100plus = [dict(row) for row in cursor.fetchall()]

            # Get total matches this week for context
            cursor.execute(f"""
                SELECT COUNT(DISTINCT m.id) as total_matches
                FROM matches m
                WHERE 1=1 {week_filter}
            """)
            total_matches = cursor.fetchone()['total_matches']

            result = jsonify({
                'week_start': start_of_week.strftime('%Y-%m-%d'),
                'week_end': end_of_week.strftime('%Y-%m-%d'),
                'week_offset': week_offset,
                'total_matches': total_matches,
                'division': division,
                'top_averages': top_averages,
                'top_checkouts': top_checkouts,
                'shortest_sets': shortest_sets,
                'most_100plus': most_100plus
            })

            if cache_backend:
                cache_backend.set(cache_key, result)
            return result

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@league_bp.route('/api/available-weeks')
def get_available_weeks():
    """API endpoint to get list of weeks (or rounds for riksserien) that have match data"""
    cache_backend = _get_cache_backend()
    cache_key = f"available_weeks_{request.query_string.decode()}"
    if cache_backend:
        cached = cache_backend.get(cache_key)
        if cached is not None:
            return cached

    try:
        league = request.args.get('league', '')

        with sqlite3.connect(_get_current_db_path()) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            if league == 'riksserien':
                # Riksserien: group matches into rounds (clusters of matches played close together)
                cursor.execute("""
                    SELECT DISTINCT DATE(match_date) as play_date, COUNT(*) as match_count
                    FROM matches
                    WHERE match_date IS NOT NULL
                    GROUP BY DATE(match_date)
                    ORDER BY play_date ASC
                """)
                dates = cursor.fetchall()

                if not dates:
                    return jsonify({'weeks': []})

                # Cluster dates into rounds (gap > 14 days = new round)
                rounds = []
                current_round_dates = [dates[0]]

                for i in range(1, len(dates)):
                    prev_date = datetime.strptime(current_round_dates[-1]['play_date'], '%Y-%m-%d')
                    curr_date = datetime.strptime(dates[i]['play_date'], '%Y-%m-%d')

                    if (curr_date - prev_date).days > 14:
                        rounds.append(current_round_dates)
                        current_round_dates = [dates[i]]
                    else:
                        current_round_dates.append(dates[i])

                rounds.append(current_round_dates)

                # Build response (most recent round first)
                weeks = []
                for idx, round_dates in enumerate(reversed(rounds)):
                    round_num = len(rounds) - idx
                    round_start = round_dates[0]['play_date']
                    round_end = round_dates[-1]['play_date']
                    match_count = sum(d['match_count'] for d in round_dates)

                    start_dt = datetime.strptime(round_start, '%Y-%m-%d')
                    end_dt = datetime.strptime(round_end, '%Y-%m-%d')

                    weeks.append({
                        'week_offset': idx,  # index in the list (0 = most recent)
                        'week_start': round_start,
                        'week_end': round_end,
                        'match_count': match_count,
                        'label': f"Omg\u00e5ng {round_num} ({start_dt.strftime('%d/%m')} - {end_dt.strftime('%d/%m')})",
                        'round_number': round_num
                    })

                result = jsonify({'weeks': weeks})
                if cache_backend:
                    cache_backend.set(cache_key, result, timeout=3600)
                return result

            # Stockholmsserien: original weekly logic
            cursor.execute("""
                SELECT MIN(match_date) as earliest, MAX(match_date) as latest
                FROM matches
            """)
            result = cursor.fetchone()

            if not result['earliest'] or not result['latest']:
                return jsonify({'weeks': []})

            earliest_date = datetime.strptime(result['earliest'][:10], '%Y-%m-%d')
            latest_date = datetime.strptime(result['latest'][:10], '%Y-%m-%d')

            # Get current week start
            today = datetime.now()
            current_week_start = today - timedelta(days=today.weekday())
            current_week_start = current_week_start.replace(hour=0, minute=0, second=0, microsecond=0)

            # Generate list of weeks from current week back to earliest data
            weeks = []
            week_start = current_week_start
            week_offset = 0

            while week_start >= earliest_date - timedelta(days=7):
                week_end = week_start + timedelta(days=6)

                # Check if there are any matches in this week
                cursor.execute("""
                    SELECT COUNT(*) as match_count
                    FROM matches
                    WHERE match_date >= ? AND match_date <= ?
                """, (week_start.strftime('%Y-%m-%d'), week_end.strftime('%Y-%m-%d 23:59:59')))
                match_count = cursor.fetchone()['match_count']

                if match_count > 0:
                    weeks.append({
                        'week_offset': week_offset,
                        'week_start': week_start.strftime('%Y-%m-%d'),
                        'week_end': week_end.strftime('%Y-%m-%d'),
                        'match_count': match_count,
                        'label': f"v.{week_start.isocalendar()[1]} ({week_start.strftime('%d/%m')} - {week_end.strftime('%d/%m')})"
                    })

                week_start = week_start - timedelta(weeks=1)
                week_offset -= 1

                # Limit to last 52 weeks
                if len(weeks) >= 52:
                    break

            response = jsonify({'weeks': weeks})
            if cache_backend:
                cache_backend.set(cache_key, response, timeout=3600)
            return response

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@league_bp.route('/api/teams')
def get_teams():
    """API endpoint to get all team names with season info for autocomplete"""
    try:
        with sqlite3.connect(_get_current_db_path()) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # Get all team names with their seasons and divisions
            # Only show combinations that have at least 1 match
            cursor.execute("""
                SELECT DISTINCT
                    t.name as team_name,
                    m.season,
                    m.division,
                    COUNT(m.id) as matches_count,
                    CASE
                        WHEN m.division = 'Unknown' OR m.division IS NULL THEN
                            t.name || ' (' || REPLACE(m.season, '/', '-') || ')'
                        WHEN t.name LIKE '%(%' THEN
                            -- Team name already contains division, just add season
                            t.name || ' (' || REPLACE(m.season, '/', '-') || ')'
                        ELSE
                            -- Team name doesn't contain division, add both division and season
                            t.name || ' (' || m.division || ') (' || REPLACE(m.season, '/', '-') || ')'
                    END as display_name
                FROM teams t
                JOIN matches m ON (t.id = m.team1_id OR t.id = m.team2_id)
                WHERE m.season IS NOT NULL
                GROUP BY t.name, m.season, m.division
                HAVING COUNT(m.id) >= 1
                ORDER BY t.name, m.season DESC, m.division
            """)

            teams = []
            for row in cursor.fetchall():
                teams.append(row['display_name'])

            return jsonify(teams)

    except Exception as e:
        return jsonify({'error': str(e)}), 500
