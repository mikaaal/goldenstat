"""
Cache warmup script - Pre-populate cache at app startup
"""
import sqlite3
import time
from datetime import datetime

def warmup_cache(app, cache):
    """
    Pre-populate cache with common queries at app startup
    """
    print("\n" + "=" * 60)
    print("CACHE WARMUP STARTED")
    print("=" * 60)
    start_time = time.time()

    with app.app_context():
        # Get list of all divisions for current season
        with sqlite3.connect('goldenstat.db') as conn:
            cursor = conn.cursor()

            # Get current season
            cursor.execute("""
                SELECT season
                FROM matches
                WHERE season IS NOT NULL
                ORDER BY match_date DESC
                LIMIT 1
            """)
            current_season_row = cursor.fetchone()

            if not current_season_row:
                print("No data found - skipping warmup")
                return

            current_season = current_season_row[0]

            # Get all divisions for current season
            cursor.execute("""
                SELECT DISTINCT division
                FROM matches
                WHERE division IS NOT NULL AND season = ?
                ORDER BY division
            """, (current_season,))
            divisions = [row[0] for row in cursor.fetchall()]

        print(f"Current season: {current_season}")
        print(f"Found {len(divisions)} divisions to warm up")

        # Warm up weekly-stats
        print("\nWarming up /api/weekly-stats...")
        warmup_count = 0

        # 1. Weekly stats without filter
        print("  - All divisions...")
        with app.test_client() as client:
            response = client.get('/api/weekly-stats')
            if response.status_code == 200:
                warmup_count += 1
                print(f"    OK - Cached")
            else:
                print(f"    FAILED ({response.status_code})")

        # 2. Weekly stats for each division
        for division in divisions:  # Cache all divisions
            print(f"  - Division: {division}...")
            with app.test_client() as client:
                response = client.get(f'/api/weekly-stats?division={division}')
                if response.status_code == 200:
                    warmup_count += 1
                    print(f"    OK - Cached")
                else:
                    print(f"    FAILED ({response.status_code})")

        # Warm up top-stats
        print("\nWarming up /api/top-stats...")

        # 1. All-time top stats
        print("  - All time...")
        with app.test_client() as client:
            response = client.get('/api/top-stats')
            if response.status_code == 200:
                warmup_count += 1
                print(f"    OK - Cached")
            else:
                print(f"    FAILED ({response.status_code})")

        # 2. Current season top stats
        print(f"  - Season: {current_season}...")
        with app.test_client() as client:
            response = client.get(f'/api/top-stats?season={current_season}')
            if response.status_code == 200:
                warmup_count += 1
                print(f"    OK - Cached")
            else:
                print(f"    FAILED ({response.status_code})")

        # 3. Previous season (if exists)
        if current_season:
            # Try to get previous season
            with sqlite3.connect('goldenstat.db') as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT DISTINCT season
                    FROM matches
                    WHERE season IS NOT NULL AND season < ?
                    ORDER BY season DESC
                    LIMIT 1
                """, (current_season,))
                prev_season_row = cursor.fetchone()

                if prev_season_row:
                    prev_season = prev_season_row[0]
                    print(f"  - Season: {prev_season}...")
                    with app.test_client() as client:
                        response = client.get(f'/api/top-stats?season={prev_season}')
                        if response.status_code == 200:
                            warmup_count += 1
                            print(f"    OK - Cached")
                        else:
                            print(f"    FAILED ({response.status_code})")

    elapsed = time.time() - start_time
    print("\n" + "=" * 60)
    print(f"CACHE WARMUP COMPLETED")
    print(f"  Entries cached: {warmup_count}")
    print(f"  Time taken: {elapsed:.2f}s")
    print("=" * 60 + "\n")
