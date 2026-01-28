#!/usr/bin/env python3
"""
GoldenStat Web Application
A Flask web app for viewing dart player statistics
"""

from flask import Flask, render_template, request, jsonify
from flask_caching import Cache
import json
import sqlite3
import logging
from datetime import datetime
from database import DartDatabase

# Configure usage logging
usage_logger = logging.getLogger('usage')
usage_logger.setLevel(logging.INFO)
# Log to file locally
usage_file_handler = logging.FileHandler('usage.log')
usage_file_handler.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))
usage_logger.addHandler(usage_file_handler)
# Log to stdout for Railway/production
usage_console_handler = logging.StreamHandler()
usage_console_handler.setFormatter(logging.Formatter('[USAGE] %(message)s'))
usage_logger.addHandler(usage_console_handler)

def get_effective_sub_match_query(player_name):
    """
    Get SQL query fragments for including sub-matches with mappings applied.
    Returns a WHERE clause that includes both direct matches and mapped sub-matches.
    """
    # Get player ID for exclusion logic
    db_path = os.getenv('DATABASE_PATH', 'goldenstat.db')
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM players WHERE name = ?", (player_name,))
        result = cursor.fetchone()
        player_id = result[0] if result else None
    
    if not player_id:
        return "p.name = ?", [player_name]
    
    # Base condition - exclude mapped-away sub-matches from base player
    base_condition = f"""(p.name = ? AND smp.sub_match_id NOT IN (
        SELECT smpm.sub_match_id 
        FROM sub_match_player_mappings smpm 
        WHERE smpm.original_player_id = {player_id}
    ))"""
    
    # Add condition for mapped sub-matches where this player should get credit
    mapped_condition = """
        OR (smp.sub_match_id IN (
            SELECT smpm.sub_match_id 
            FROM sub_match_player_mappings smpm 
            WHERE smpm.correct_player_name = ?
        ) AND smp.player_id IN (
            SELECT DISTINCT smpm2.original_player_id 
            FROM sub_match_player_mappings smpm2 
            WHERE smpm2.correct_player_name = ?
        ))
    """
    
    return f"({base_condition} {mapped_condition})", [player_name, player_name, player_name]

def get_effective_player_ids(cursor, player_name):
    """
    Get player ID for the given player name.
    Sub-match mappings are handled in the SQL queries, not here.
    """
    cursor.execute("SELECT id FROM players WHERE name = ?", (player_name,))
    result = cursor.fetchone()
    return [result['id']] if result else []

app = Flask(__name__)
app.secret_key = 'goldenstat-secret-key'

# Configure caching
# Use FileSystemCache (persists across process restarts, works with Flask reloader)
import os
cache = Cache(app, config={
    'CACHE_TYPE': 'FileSystemCache',
    'CACHE_DIR': '.flask_cache',
    'CACHE_DEFAULT_TIMEOUT': 0  # No timeout - cache until manually cleared or app redeployed
})

# Use DATABASE_PATH environment variable if set (for Railway persistent volume)
db_path = os.getenv('DATABASE_PATH', 'goldenstat.db')
db = DartDatabase(db_path=db_path)

# Global flag to track if warmup has run
_warmup_done = False
_warmup_disabled = False

# Initialize cache warmup for production (Gunicorn/Railway)
def init_app():
    """Initialize app - called once on startup in production"""
    try:
        from cache_warmup import warmup_cache
        warmup_cache(app, cache)
        global _warmup_done
        _warmup_done = True
    except Exception as e:
        print(f"Cache warmup failed (non-critical): {e}")

@app.route('/')
def index():
    """Main page with player search"""
    return render_template('index.html')


@app.route('/api/last-import')
def get_last_import():
    """API endpoint to get last import info"""
    try:
        import os
        import json
        import glob
        from datetime import datetime

        log_dir = 'import_logs'
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


@app.route('/api/track-tab', methods=['POST'])
def track_tab_click():
    """Log tab clicks for usage analytics"""
    try:
        data = request.get_json()
        tab = data.get('tab', 'unknown')
        context = data.get('context', '')

        # Get client info
        ip = request.headers.get('X-Forwarded-For', request.remote_addr)
        user_agent = request.headers.get('User-Agent', '')[:100]

        usage_logger.info(f"TAB | {tab} | context={context} | ip={ip} | ua={user_agent}")

        return jsonify({'status': 'ok'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/teams')
def get_teams():
    """API endpoint to get all team names with season info for autocomplete"""
    try:
        import sqlite3
        with sqlite3.connect(db.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Get all team names with their seasons and divisions
            # Only show combinations that have at least 1 match
            # Filter out Unknown divisions
            cursor.execute("""
                SELECT DISTINCT
                    t.name as team_name,
                    m.season,
                    m.division,
                    COUNT(m.id) as matches_count,
                    CASE
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
                    AND m.division IS NOT NULL
                    AND m.division != 'Unknown'
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

@app.route('/api/top-stats')
@cache.cached(query_string=True)  # Cache indefinitely until redeploy, vary by season param
def get_top_stats():
    """API endpoint to get top statistics"""
    try:
        import sqlite3
        with sqlite3.connect(db.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # Get optional season filter from query parameter
            season = request.args.get('season')
            season_filter = ""
            if season:
                season_filter = f"AND m.season = '{season}'"

            # Top 10 highest averages in a single match (Singles only)
            # Use player_avg from sub_match_participants (already calculated correctly)
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
            # Checkout value is the remaining_score from the PREVIOUS throw
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
            # Count total darts for winning team, only for completed legs
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
            # Note: throws table doesn't have player_id, we need to infer from team_number
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

            return jsonify({
                'top_averages': top_averages,
                'top_checkouts': top_checkouts,
                'shortest_sets': shortest_sets,
                'most_180s': most_180s
            })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/weekly-stats')
@cache.cached(query_string=True)  # Cache indefinitely until redeploy, vary by division param
def get_weekly_stats():
    """API endpoint to get statistics for the current week"""
    try:
        import sqlite3
        from datetime import datetime, timedelta
        with sqlite3.connect(db.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # Get optional division filter from query parameter
            division = request.args.get('division')

            # Calculate current week's date range (Monday to Sunday)
            today = datetime.now()
            # Get the start of the week (Monday)
            start_of_week = today - timedelta(days=today.weekday())
            start_of_week = start_of_week.replace(hour=0, minute=0, second=0, microsecond=0)
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

            return jsonify({
                'week_start': start_of_week.strftime('%Y-%m-%d'),
                'week_end': end_of_week.strftime('%Y-%m-%d'),
                'total_matches': total_matches,
                'division': division,
                'top_averages': top_averages,
                'top_checkouts': top_checkouts,
                'shortest_sets': shortest_sets,
                'most_100plus': most_100plus
            })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/track-tab', methods=['POST'])
def track_tab():
    """Track tab navigation for analytics"""
    try:
        data = request.get_json()
        tab_name = data.get('tab', 'unknown')
        client_ip = request.remote_addr
        user_agent = request.headers.get('User-Agent', 'unknown')

        # Log to console/file
        app.logger.info(f"Tab navigation: {tab_name} | IP: {client_ip} | User-Agent: {user_agent[:50]}")

        return jsonify({'status': 'ok'}), 200
    except Exception as e:
        app.logger.error(f"Error tracking tab: {e}")
        return jsonify({'status': 'error'}), 500

@app.route('/api/track-click', methods=['POST'])
def track_click():
    """Track click events for analytics"""
    try:
        data = request.get_json()
        event_name = data.get('event', 'unknown')
        client_ip = request.remote_addr
        user_agent = request.headers.get('User-Agent', 'unknown')

        app.logger.info(f"Click event: {event_name} | IP: {client_ip} | User-Agent: {user_agent[:50]}")

        return jsonify({'status': 'ok'}), 200
    except Exception as e:
        app.logger.error(f"Error tracking click: {e}")
        return jsonify({'status': 'error'}), 500

@app.route('/api/track-pageview', methods=['POST'])
def track_pageview():
    """Track page views for analytics"""
    try:
        data = request.get_json()
        page_name = data.get('page', 'unknown')
        client_ip = request.remote_addr
        user_agent = request.headers.get('User-Agent', 'unknown')

        app.logger.info(f"Page view: {page_name} | IP: {client_ip} | User-Agent: {user_agent[:50]}")

        return jsonify({'status': 'ok'}), 200
    except Exception as e:
        app.logger.error(f"Error tracking pageview: {e}")
        return jsonify({'status': 'error'}), 500

@app.route('/api/divisions')
def get_divisions():
    """API endpoint to get all divisions for current season"""
    try:
        import sqlite3
        with sqlite3.connect(db.db_path) as conn:
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

            # Custom sort: SL6 first, then SL4, then rest in ascending order, Mixed last
            sl_divisions = [d for d in divisions if d in ["SL6", "SL4"]]
            mixed_divisions = [d for d in divisions if "Mixed" in d]
            other_divisions = [d for d in divisions if d not in ["SL6", "SL4"] and "Mixed" not in d]

            # Sort other divisions in ascending order (1A, 1FA, 1FB, ... 4FA)
            other_divisions.sort()

            # Combine: SL6, SL4, others ascending, Mixed last
            return jsonify(sl_divisions + other_divisions + mixed_divisions)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/players')
def get_players():
    """API endpoint to get all player names for autocomplete"""
    try:
        import sqlite3
        with sqlite3.connect(db.db_path) as conn:
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

@app.route('/api/player/<player_name>')
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
        with sqlite3.connect("goldenstat.db") as temp_conn:
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
        
        stats = db.get_player_stats(player_name, season=season, division=division, team_filter=None)
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

@app.route('/api/player/<player_name>/detailed')
def get_player_detailed_stats(player_name):
    """Get detailed player statistics including match history and trends"""
    try:
        # URL decode the player name first
        from urllib.parse import unquote
        player_name = unquote(player_name)

        import sqlite3
        with sqlite3.connect(db.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Get all effective player IDs (including mapped ones)
            all_player_ids = get_effective_player_ids(cursor, player_name)
            if not all_player_ids:
                return jsonify({'error': 'Player not found'}), 404
            
            # Get detailed match history with averages over time
            cursor.execute("""
                SELECT 
                    m.match_date,
                    t1.name as team1_name,
                    t2.name as team2_name,
                    sm.match_type,
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

@app.route('/player/<player_name>')
def player_detail(player_name):
    """Player detail page"""
    return render_template('player_detail.html', player_name=player_name)

@app.route('/sub_match_throws')
def sub_match_throws():
    """Sub-match throws visualization page"""
    return render_template('sub_match_throws.html')

@app.route('/test_throws')
def test_throws():
    """Test page for throws visualization"""
    return render_template('test_throws.html')

@app.route('/api/leagues')
def get_leagues():
    """Get available leagues and seasons"""
    try:
        import sqlite3
        with sqlite3.connect(db.db_path) as conn:
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

@app.route('/api/overview')
def get_overview():
    """Get database overview statistics"""
    try:
        import sqlite3
        with sqlite3.connect(db.db_path) as conn:
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

@app.route('/api/player/<player_name>/throws')
def get_player_throws(player_name):
    """Get detailed throw analysis for a player"""
    try:
        # URL decode the player name first
        from urllib.parse import unquote
        player_name = unquote(player_name)

        import sqlite3
        with sqlite3.connect(db.db_path) as conn:
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
            player_ids = get_effective_player_ids(cursor, player_name)

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
                ) AND sm.match_type = 'Singles'"""
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
                    '0-20': len([s for s in scores if 0 <= s <= 20]),
                    '21-40': len([s for s in scores if 21 <= s <= 40]),
                    '41-60': len([s for s in scores if 41 <= s <= 60]),
                    '61-80': len([s for s in scores if 61 <= s <= 80]),
                    '81-99': len([s for s in scores if 81 <= s <= 99]),
                    '100+': len([s for s in scores if s >= 100])
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
                from collections import defaultdict
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
                from collections import Counter
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
                    ) AND sm.match_type = 'Singles'"""
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

                    all_time_statistics = {
                        'throws_over_100': all_time_throws_over_100,
                        'throws_over_140': all_time_throws_over_140,
                        'throws_180': all_time_throws_180,
                        'high_finishes': all_time_high_finishes
                    }
            else:
                # No filters applied, use current statistics as all-time
                all_time_statistics = {
                    'throws_over_100': statistics.get('throws_over_100', 0),
                    'throws_over_140': statistics.get('throws_over_140', 0),
                    'throws_180': statistics.get('throws_180', 0),
                    'high_finishes': statistics.get('high_finishes', 0)
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

@app.route('/api/sub_match/<int:sub_match_id>')
def get_sub_match_info(sub_match_id):
    """Get basic sub-match information with corrected player names"""
    try:
        import sqlite3
        with sqlite3.connect(db.db_path) as conn:
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

@app.route('/api/sub_match/<int:sub_match_id>/throws/<player_name>')
def get_sub_match_player_throws(sub_match_id, player_name):
    """Get detailed throw data for a specific player in a specific sub-match"""
    try:
        import sqlite3
        from urllib.parse import unquote
        player_name = unquote(player_name)

        # Handle team disambiguation like "Robban (Bålsta)" -> "Robban"
        with sqlite3.connect(db.db_path) as temp_conn:
            temp_cursor = temp_conn.cursor()
            temp_cursor.execute("SELECT id FROM players WHERE name = ?", (player_name,))
            is_exact_match = temp_cursor.fetchone() is not None

        if '(' in player_name and player_name.endswith(')') and not is_exact_match:
            player_name = player_name.split(' (')[0]

        with sqlite3.connect(db.db_path) as conn:
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
            
            opponent_names = ' / '.join(opponents) if len(opponents) > 1 else (opponents[0] if opponents else 'Okänd')
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
                
                # Calculate "Första 9 pil" (first 3 rounds average across all legs)
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

@app.route('/api/team/<path:team_name>/lineup')
def get_team_lineup(team_name):
    """Get team lineup prediction based on historical position data"""
    try:
        import sqlite3
        with sqlite3.connect(db.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Get filter parameters
            season = request.args.get('season')
            division = None
            
            # Handle new team name format: "Team (Division) (Season)" or "Team Name (Season)"
            import re
            
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
            
            return jsonify({
                'team_name': team_name,
                'total_matches': total_matches,
                'season': season,
                'division': division,
                'positions': formatted_positions
            })
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/team/<path:team_name>/players')
def get_team_players(team_name):
    """Get all players who have played for a team"""
    try:
        import sqlite3
        with sqlite3.connect(db.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # Get filter parameters
            season = request.args.get('season')
            division = None

            # Handle team name format with season/division
            import re

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

@app.route('/api/team/<path:team_name>/doubles-pairs')
def get_team_doubles_pairs(team_name):
    """Get doubles pair statistics for a team - who played with whom and at which position"""
    try:
        import sqlite3
        import re
        from collections import defaultdict

        with sqlite3.connect(db.db_path) as conn:
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

@app.route('/api/club/<path:club_name>/players')
def get_club_players(club_name):
    """Get all players who have played for any team in a club (across all divisions)"""
    try:
        import sqlite3
        import re
        with sqlite3.connect(db.db_path) as conn:
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


@app.route('/api/match/<int:match_id>/legs')
def get_match_legs(match_id):
    """Get detailed leg information for a match"""
    try:
        import sqlite3
        with sqlite3.connect(db.db_path) as conn:
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


@app.route('/api/player/<int:player_id>/memorable-matches')
def get_memorable_matches(player_id):
    """Hämta de tre mest minnesvärda matcherna för en spelare baserat på pilsnitt, korta set och höga utgångar"""
    try:
        with sqlite3.connect("goldenstat.db") as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # Hämta alla singelmatcher för spelaren med detaljerad statistik
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
                WHERE smp.player_id = ? AND sm.match_type = 'Singles'
                ORDER BY m.match_date DESC
            """, (player_id,))

            matches = cursor.fetchall()
            memorable_matches = []

            for match in matches:
                sub_match_id = match['sub_match_id']

                # Hämta kastdata för denna match
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

                # Beräkna statistik för denna match
                total_score = sum(t['score'] for t in throws)
                total_throws = len(throws)
                average_score = total_score / total_throws if total_throws > 0 else 0

                # Räkna höga utgångar (100+) - kolla föregående kasts remaining_score
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

                # Räkna korta set (≤18 kast per leg)
                leg_throws = {}
                for throw in throws:
                    leg_id = throw['leg_id']
                    if leg_id not in leg_throws:
                        leg_throws[leg_id] = 0
                    leg_throws[leg_id] += 1

                short_sets = sum(1 for count in leg_throws.values() if count <= 18)

                # Beräkna "minnesvärdhet" - kombinera pilsnitt, korta set och höga utgångar
                # Normalisera värdena och ge dem vikter
                memorability_score = (
                    (average_score / 50.0) * 0.4 +  # Pilsnitt (normaliserat mot 50)
                    (short_sets * 2.0) * 0.3 +       # Korta set (2 poäng per kort set)
                    (high_finishes * 3.0) * 0.3      # Höga utgångar (3 poäng per hög utgång)
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

            # Sortera efter minnesvärdhet och ta de tre bästa
            memorable_matches.sort(key=lambda x: x['memorability_score'], reverse=True)
            top_3_matches = memorable_matches[:3]

            return jsonify({
                'memorable_matches': top_3_matches
            })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/match_overview')
def match_overview():
    """Page to show all sub-matches in a series match"""
    return render_template('match_overview.html')


@app.route('/api/match/<int:match_id>/overview')
def get_match_overview(match_id):
    """Get overview of all sub-matches in a series match"""
    try:
        import sqlite3
        with sqlite3.connect(db.db_path) as conn:
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
                position = parse_match_position(sm['match_name'], sm['match_type'])

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

                sub_matches.append({
                    'id': sm['id'],
                    'position': position,
                    'match_type': sm['match_type'],
                    'team1_players': ' / '.join(team1_players),
                    'team2_players': ' / '.join(team2_players),
                    'team1_legs': sm['team1_legs'],
                    'team2_legs': sm['team2_legs'],
                    'team1_avg': round(team1_avg, 2) if team1_avg else None,
                    'team2_avg': round(team2_avg, 2) if team2_avg else None
                })

            # Sort sub_matches by position order: D1, S1, S2, D2, S3, S4, D3, S5, S6, AD (AD always last)
            position_order = {
                'D1': 1, 'S1': 2, 'S2': 3, 'D2': 4, 'S3': 5, 'S4': 6,
                'D3': 7, 'S5': 8, 'S6': 9,
                'AD': 100  # AD always last
            }
            sub_matches.sort(key=lambda x: position_order.get(x['position'], 50))

            # Calculate sub-match wins for each team
            team1_sub_wins = sum(1 for sm in sub_matches if sm['team1_legs'] > sm['team2_legs'])
            team2_sub_wins = sum(1 for sm in sub_matches if sm['team2_legs'] > sm['team1_legs'])

            return jsonify({
                'match_info': dict(match_info),
                'sub_matches': sub_matches,
                'team1_sub_wins': team1_sub_wins,
                'team2_sub_wins': team2_sub_wins
            })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


def parse_match_position(match_name, match_type):
    """Parse match position (D1, S1, S2, D2, S3, S4, AD) from match_name"""
    if not match_name:
        return 'S1' if match_type == 'Singles' else 'D1'

    # Check for AD first
    if ' AD' in match_name:
        return 'AD'

    # Extract Singles/Doubles number
    if 'Singles' in match_name:
        import re
        match = re.search(r'Singles(\d+)', match_name)
        return f'S{match.group(1)}' if match else 'S1'
    elif 'Doubles' in match_name:
        import re
        match = re.search(r'Doubles(\d+)', match_name)
        return f'D{match.group(1)}' if match else 'D1'

    # Fallback
    return 'S1' if match_type == 'Singles' else 'D1'


@app.route('/api/sub_match/<int:sub_match_id>/match_id')
def get_sub_match_match_id(sub_match_id):
    """Get the parent match_id for a sub_match"""
    try:
        import sqlite3
        with sqlite3.connect(db.db_path) as conn:
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


@app.route('/series_matches')
def series_matches():
    """Page to show all series matches grouped by week"""
    return render_template('series_matches.html')


@app.route('/api/series_matches')
def get_series_matches():
    """Get all series matches grouped by week"""
    try:
        import sqlite3
        from datetime import datetime

        # Get filter parameters
        season = request.args.get('season')
        division = request.args.get('division')

        with sqlite3.connect(db.db_path) as conn:
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
                    (SELECT COUNT(*) FROM sub_matches sm WHERE sm.match_id = m.id AND sm.team1_legs > sm.team2_legs) as team1_sub_wins,
                    (SELECT COUNT(*) FROM sub_matches sm WHERE sm.match_id = m.id AND sm.team2_legs > sm.team1_legs) as team2_sub_wins
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
                        week_label = "Okänt datum"
                else:
                    week_key = "unknown"
                    week_label = "Okänt datum"

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


if __name__ == '__main__':
    import sys
    import os
    import threading
    import time

    print("Starting GoldenStat Web Application...")

    # Check if running in production (Railway sets RAILWAY_ENVIRONMENT)
    is_production = os.environ.get('RAILWAY_ENVIRONMENT') or os.environ.get('FLASK_ENV') == 'production'
    debug_mode = not is_production

    # Check for --no-warmup flag
    if '--no-warmup' in sys.argv:
        _warmup_disabled = True
        print("Cache warmup disabled (--no-warmup flag)")
    else:
        # Start warmup in background thread after Flask starts
        def delayed_warmup():
            # Wait for Flask to start
            time.sleep(3)
            # In production (no debug/reloader), always run warmup
            # In development, only run in child process (after reloader)
            should_run = (not debug_mode) or (os.environ.get('WERKZEUG_RUN_MAIN') == 'true')

            if should_run:
                try:
                    print("\n" + "="*60)
                    print("Starting cache warmup in background...")
                    print("="*60)
                    from cache_warmup import warmup_cache
                    warmup_cache(app, cache)
                except Exception as e:
                    print(f"Cache warmup failed: {e}")

        warmup_thread = threading.Thread(target=delayed_warmup, daemon=True)
        warmup_thread.start()

    if debug_mode:
        print("Open your browser to: http://localhost:3000")
    else:
        print("Production mode - cache warmup will start in 3 seconds...")

    app.run(debug=debug_mode, host='0.0.0.0', port=3000)