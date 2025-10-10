import sqlite3
from datetime import datetime, timedelta
import time

conn = sqlite3.connect('goldenstat.db')
cursor = conn.cursor()

# Calculate current week
today = datetime.now()
start_of_week = today - timedelta(days=today.weekday())
start_of_week = start_of_week.replace(hour=0, minute=0, second=0, microsecond=0)
end_of_week = start_of_week + timedelta(days=6, hours=23, minutes=59, seconds=59)

week_filter = f"AND m.match_date >= '{start_of_week.strftime('%Y-%m-%d %H:%M:%S')}' AND m.match_date <= '{end_of_week.strftime('%Y-%m-%d %H:%M:%S')}'"

print("=" * 80)
print("CREATING INDEXES FOR OPTIMIZATION")
print("=" * 80)

# Create indexes
indexes_to_create = [
    ("idx_throws_remaining_score", "CREATE INDEX IF NOT EXISTS idx_throws_remaining_score ON throws(remaining_score)"),
    ("idx_throws_score", "CREATE INDEX IF NOT EXISTS idx_throws_score ON throws(score)"),
    ("idx_throws_leg_team_round", "CREATE INDEX IF NOT EXISTS idx_throws_leg_team_round ON throws(leg_id, team_number, round_number)"),
]

for idx_name, sql in indexes_to_create:
    print(f"\nCreating {idx_name}...")
    start = time.time()
    cursor.execute(sql)
    conn.commit()
    elapsed = time.time() - start
    print(f"  Created in {elapsed:.4f}s")

print("\n" + "=" * 80)
print("TESTING OPTIMIZED QUERIES")
print("=" * 80)

# Query 2 OPTIMIZED: Top Checkouts
# Optimization: Filter throws first by joining with matches to limit scope
print("\n" + "=" * 60)
print("QUERY 2 (OPTIMIZED): Top Checkouts")
print("=" * 60)

query2_optimized = f"""
    SELECT
        p.name as player_name,
        prev.remaining_score as checkout,
        CASE WHEN curr.team_number = 1 THEN t1.name ELSE t2.name END as team_name,
        CASE WHEN curr.team_number = 1 THEN t2.name ELSE t1.name END as opponent_name,
        DATE(m.match_date) as match_date,
        sm.id as sub_match_id
    FROM throws curr
    JOIN legs l ON curr.leg_id = l.id
    JOIN sub_matches sm ON l.sub_match_id = sm.id
    JOIN matches m ON sm.match_id = m.id
    JOIN throws prev ON curr.leg_id = prev.leg_id
        AND curr.team_number = prev.team_number
        AND prev.round_number = curr.round_number - 1
    JOIN sub_match_participants smp ON sm.id = smp.sub_match_id AND smp.team_number = curr.team_number
    JOIN players p ON smp.player_id = p.id
    JOIN teams t1 ON m.team1_id = t1.id
    JOIN teams t2 ON m.team2_id = t2.id
    WHERE curr.remaining_score = 0
        AND prev.remaining_score > 0
        AND curr.team_number = l.winner_team
        AND sm.match_type = 'Singles'
    {week_filter}
    ORDER BY prev.remaining_score DESC, m.match_date DESC
    LIMIT 10
"""

print("Optimization: Filter by date first, then join throws")
cursor.execute(f"EXPLAIN QUERY PLAN {query2_optimized}")
plan = cursor.fetchall()
print("\nQuery Plan:")
for row in plan:
    print(f"  {row}")

start = time.time()
cursor.execute(query2_optimized)
results = cursor.fetchall()
elapsed = time.time() - start
print(f"\nExecution time: {elapsed:.4f}s")
print(f"Results returned: {len(results)}")

# Query 3 OPTIMIZED: Shortest Legs
print("\n" + "=" * 60)
print("QUERY 3 (OPTIMIZED): Shortest Legs")
print("=" * 60)

query3_optimized = f"""
    WITH weekly_matches AS (
        SELECT m.id as match_id
        FROM matches m
        WHERE 1=1 {week_filter}
    ),
    weekly_sub_matches AS (
        SELECT sm.id as sub_match_id
        FROM sub_matches sm
        JOIN weekly_matches wm ON sm.match_id = wm.match_id
        WHERE sm.match_type = 'Singles'
    ),
    weekly_legs AS (
        SELECT l.id as leg_id, l.winner_team, l.sub_match_id
        FROM legs l
        JOIN weekly_sub_matches wsm ON l.sub_match_id = wsm.sub_match_id
        WHERE EXISTS (
            SELECT 1 FROM throws t
            WHERE t.leg_id = l.id AND t.remaining_score = 0
        )
    ),
    leg_darts AS (
        SELECT
            wl.leg_id,
            wl.winner_team,
            wl.sub_match_id,
            SUM(CASE WHEN t.darts_used IS NOT NULL THEN t.darts_used ELSE 3 END) as total_darts
        FROM weekly_legs wl
        JOIN throws t ON wl.leg_id = t.leg_id AND t.team_number = wl.winner_team
        WHERE NOT (t.score = 0 AND t.remaining_score = 501)
        GROUP BY wl.leg_id, wl.winner_team, wl.sub_match_id
    )
    SELECT
        p.name as player_name,
        ld.total_darts as darts,
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
    ORDER BY ld.total_darts ASC, m.match_date DESC
    LIMIT 10
"""

print("Optimization: Filter matches first, then cascade down")
cursor.execute(f"EXPLAIN QUERY PLAN {query3_optimized}")
plan = cursor.fetchall()
print("\nQuery Plan:")
for row in plan[:15]:  # Show first 15 lines
    print(f"  {row}")
if len(plan) > 15:
    print(f"  ... ({len(plan) - 15} more lines)")

start = time.time()
cursor.execute(query3_optimized)
results = cursor.fetchall()
elapsed = time.time() - start
print(f"\nExecution time: {elapsed:.4f}s")
print(f"Results returned: {len(results)}")

# Query 4 OPTIMIZED: Most 100+ throws
print("\n" + "=" * 60)
print("QUERY 4 (OPTIMIZED): Most 100+ Throws")
print("=" * 60)

query4_optimized = f"""
    WITH weekly_matches AS (
        SELECT m.id as match_id
        FROM matches m
        WHERE 1=1 {week_filter}
    ),
    weekly_sub_matches AS (
        SELECT sm.id as sub_match_id
        FROM sub_matches sm
        JOIN weekly_matches wm ON sm.match_id = wm.match_id
        WHERE sm.match_type = 'Singles'
    ),
    match_100plus AS (
        SELECT
            wsm.sub_match_id,
            t.team_number,
            COUNT(*) as count_100plus
        FROM weekly_sub_matches wsm
        JOIN legs l ON l.sub_match_id = wsm.sub_match_id
        JOIN throws t ON t.leg_id = l.id
        WHERE t.score >= 100
        GROUP BY wsm.sub_match_id, t.team_number
    )
    SELECT
        p.name as player_name,
        m100.count_100plus,
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
    ORDER BY m100.count_100plus DESC, m.match_date DESC
    LIMIT 10
"""

print("Optimization: Filter sub-matches first, then scan throws only for those matches")
cursor.execute(f"EXPLAIN QUERY PLAN {query4_optimized}")
plan = cursor.fetchall()
print("\nQuery Plan:")
for row in plan[:15]:
    print(f"  {row}")
if len(plan) > 15:
    print(f"  ... ({len(plan) - 15} more lines)")

start = time.time()
cursor.execute(query4_optimized)
results = cursor.fetchall()
elapsed = time.time() - start
print(f"\nExecution time: {elapsed:.4f}s")
print(f"Results returned: {len(results)}")

print("\n" + "=" * 80)
print("SUMMARY")
print("=" * 80)
print("Indexes created:")
for idx_name, _ in indexes_to_create:
    print(f"  - {idx_name}")
print("\nAll queries optimized to filter by date range first")
print("This reduces the throwns table scan from 1.8M rows to only weekly data")

conn.close()
