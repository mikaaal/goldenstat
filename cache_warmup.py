"""
Cache warmup script - Pre-populate cache at app startup
"""
import sqlite3
import time
from datetime import datetime


def warmup_league(app, league_name, db_path, league_param):
    """
    Warm up cache for a specific league.
    league_param is the query string suffix, e.g. '' or '&league=riksserien'
    """
    sep = '?' if not league_param else '&'
    prefix = f"?league={league_param}" if league_param else ''

    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()

        cursor.execute("""
            SELECT season
            FROM matches
            WHERE season IS NOT NULL
            ORDER BY match_date DESC
            LIMIT 1
        """)
        current_season_row = cursor.fetchone()

        if not current_season_row:
            print(f"  No data found for {league_name} - skipping")
            return 0

        current_season = current_season_row[0]

        cursor.execute("""
            SELECT DISTINCT division
            FROM matches
            WHERE division IS NOT NULL AND season = ?
            ORDER BY division
        """, (current_season,))
        divisions = [row[0] for row in cursor.fetchall()]

        cursor.execute("""
            SELECT DISTINCT season
            FROM matches
            WHERE season IS NOT NULL AND season < ?
            ORDER BY season DESC
            LIMIT 1
        """, (current_season,))
        prev_season_row = cursor.fetchone()
        prev_season = prev_season_row[0] if prev_season_row else None

    print(f"\n  {league_name}: season={current_season}, {len(divisions)} divisions")
    warmup_count = 0

    # --- Available weeks (warm this first, then use it to warm weekly stats) ---
    print(f"  Warming up /api/available-weeks ({league_name})...")
    available_weeks = []
    with app.test_client() as client:
        url = f'/api/available-weeks{prefix}'
        response = client.get(url)
        if response.status_code == 200:
            warmup_count += 1
            available_weeks = response.get_json().get('weeks', [])
            print(f"    OK  {url} ({len(available_weeks)} weeks)")
        else:
            print(f"    FAIL {url} ({response.status_code})")

    # --- Weekly stats (warm the 6 most recent weeks) ---
    weeks_to_warm = available_weeks[:6]
    print(f"  Warming up /api/weekly-stats ({league_name}): {len(weeks_to_warm)} of {len(available_weeks)} weeks...")
    weekly_count = 0
    is_riksserien = league_param == 'riksserien'

    for i, week in enumerate(weeks_to_warm, 1):
        week_label = week.get('label', week.get('week_start', '?'))
        print(f"    [{i}/{len(weeks_to_warm)}] {week_label}...", end=' ', flush=True)

        # Build week-specific params
        if is_riksserien:
            week_params = f"date_start={week['week_start']}&date_end={week['week_end']}"
        else:
            week_params = f"week_offset={week['week_offset']}"

        week_ok = 0

        # All divisions (no filter)
        with app.test_client() as client:
            if prefix:
                url = f'/api/weekly-stats{prefix}&{week_params}'
            else:
                url = f'/api/weekly-stats?{week_params}'
            response = client.get(url)
            if response.status_code == 200:
                weekly_count += 1
                week_ok += 1

        # Per division
        for division in divisions:
            with app.test_client() as client:
                if prefix:
                    url = f'/api/weekly-stats{prefix}&{week_params}&division={division}'
                else:
                    url = f'/api/weekly-stats?{week_params}&division={division}'
                response = client.get(url)
                if response.status_code == 200:
                    weekly_count += 1
                    week_ok += 1

        print(f"{week_ok} OK")

    warmup_count += weekly_count
    print(f"    {weekly_count} weekly-stats entries cached")

    # --- Top stats ---
    print(f"  Warming up /api/top-stats ({league_name})...")
    top_count = 0

    # All-time
    with app.test_client() as client:
        url = f'/api/top-stats{prefix}'
        response = client.get(url)
        if response.status_code == 200:
            top_count += 1
            print(f"    OK  {url}")
        else:
            print(f"    FAIL {url} ({response.status_code})")

    # Current season
    with app.test_client() as client:
        url = f'/api/top-stats{prefix}{"&" if prefix else "?"}season={current_season}'
        response = client.get(url)
        if response.status_code == 200:
            top_count += 1
            print(f"    OK  {url}")
        else:
            print(f"    FAIL {url} ({response.status_code})")

    # Previous season
    if prev_season:
        with app.test_client() as client:
            url = f'/api/top-stats{prefix}{"&" if prefix else "?"}season={prev_season}'
            response = client.get(url)
            if response.status_code == 200:
                top_count += 1
                print(f"    OK  {url}")
            else:
                print(f"    FAIL {url} ({response.status_code})")

    print(f"    {top_count} top-stats entries cached")
    warmup_count += top_count
    return warmup_count


def warmup_cache(app, cache):
    """
    Pre-populate cache with common queries at app startup
    """
    print("\n" + "=" * 60)
    print("CACHE WARMUP STARTED")
    print("=" * 60)
    start_time = time.time()

    total = 0
    with app.app_context():
        # Stockholmsserien (default league)
        total += warmup_league(app, "Stockholmsserien", 'goldenstat.db', '')

        # Riksserien
        total += warmup_league(app, "Riksserien", 'riksserien.db', 'riksserien')

    elapsed = time.time() - start_time
    print("\n" + "=" * 60)
    print(f"CACHE WARMUP COMPLETED")
    print(f"  Entries cached: {total}")
    print(f"  Time taken: {elapsed:.1f}s")
    print("=" * 60 + "\n")
