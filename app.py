#!/usr/bin/env python3
"""
GoldenStat Web Application
A Flask web app for viewing dart player statistics
"""

from flask import Flask, request
from flask_caching import Cache
import os
import re
import sqlite3
import logging
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


# --- Shared helpers (used by route blueprints) ---

def get_effective_sub_match_query(player_name):
    """
    Get SQL query fragments for including sub-matches with mappings applied.
    Returns a WHERE clause that includes both direct matches and mapped sub-matches.
    """
    current_db_path = get_current_db_path()
    with sqlite3.connect(current_db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM players WHERE name = ?", (player_name,))
        result = cursor.fetchone()
        player_id = result[0] if result else None

    if not player_id:
        return "p.name = ?", [player_name]

    base_condition = f"""(p.name = ? AND smp.sub_match_id NOT IN (
        SELECT smpm.sub_match_id
        FROM sub_match_player_mappings smpm
        WHERE smpm.original_player_id = {player_id}
    ))"""

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


def parse_match_position(match_name, match_type):
    """Parse match position (D1, S1, S2, D2, S3, S4, AD) from match_name"""
    if not match_name:
        return 'S1' if match_type == 'Singles' else 'D1'

    if ' AD' in match_name:
        return 'AD'

    singles_match = re.search(r'(?:Singles|Singel)\s*(\d+)', match_name)
    if singles_match:
        return f'S{singles_match.group(1)}'

    doubles_match = re.search(r'(?:Doubles|Dubbel)\s*(\d+)', match_name)
    if doubles_match:
        return f'D{doubles_match.group(1)}'

    return 'S1' if match_type == 'Singles' else 'D1'


# --- Flask app setup ---

app = Flask(__name__)
app.secret_key = 'goldenstat-secret-key'

# Configure caching
cache = Cache(app, config={
    'CACHE_TYPE': 'FileSystemCache',
    'CACHE_DIR': '.flask_cache',
    'CACHE_DEFAULT_TIMEOUT': 0
})

# Use DATABASE_PATH environment variable if set (for Railway persistent volume)
db_path = os.getenv('DATABASE_PATH', 'goldenstat.db')
db = DartDatabase(db_path=db_path)


def get_current_db_path():
    """Get the database path for the current request based on league parameter"""
    league = request.args.get('league', '')
    if league == 'riksserien':
        return 'riksserien.db'
    return db.db_path


def get_current_db():
    """Get the DartDatabase instance for the current request"""
    league = request.args.get('league', '')
    if league == 'riksserien':
        return DartDatabase(db_path='riksserien.db')
    return db


# --- Register blueprints ---

from routes.tracking import tracking_bp
from routes.tournaments import tournaments_bp
from routes.teams import teams_bp
from routes.players import players_bp
from routes.matches import matches_bp
from routes.league import league_bp

app.register_blueprint(tracking_bp)
app.register_blueprint(tournaments_bp)
app.register_blueprint(teams_bp)
app.register_blueprint(players_bp)
app.register_blueprint(matches_bp)
app.register_blueprint(league_bp)


# --- Cache warmup ---

_warmup_done = False
_warmup_disabled = False


def init_app():
    """Initialize app - called once on startup in production"""
    try:
        from cache_warmup import warmup_cache
        warmup_cache(app, cache)
        global _warmup_done
        _warmup_done = True
    except Exception as e:
        print(f"Cache warmup failed (non-critical): {e}")


# --- Startup ---

if __name__ == '__main__':
    import sys
    import threading
    import time

    print("Starting GoldenStat Web Application...")

    is_production = os.environ.get('RAILWAY_ENVIRONMENT') or os.environ.get('FLASK_ENV') == 'production'
    debug_mode = not is_production

    if '--no-warmup' in sys.argv:
        _warmup_disabled = True
        print("Cache warmup disabled (--no-warmup flag)")
    else:
        def delayed_warmup():
            time.sleep(3)
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
