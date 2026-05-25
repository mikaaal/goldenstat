# -*- coding: utf-8 -*-
import sqlite3
import sys
sys.stdout.reconfigure(encoding='utf-8')

conn = sqlite3.connect("riksserien.db")
cursor = conn.cursor()

print("=== RIKSSERIEN 2025/2026 EFTER IMPORT ===\n")

print("--- Speldagar nu i DB ---")
cursor.execute("""
    SELECT DATE(match_date) as datum, COUNT(*) as antal
    FROM matches
    WHERE season = '2025/2026'
    GROUP BY DATE(match_date)
    ORDER BY datum
""")
for row in cursor.fetchall():
    print(f"  {row[0]}: {row[1]} matcher")

print("\n--- Matcher per division (totalt och senaste) ---")
cursor.execute("""
    SELECT division, COUNT(*) as antal,
           MAX(DATE(match_date)) as senaste
    FROM matches
    WHERE season = '2025/2026'
    GROUP BY division
    ORDER BY division
""")
for row in cursor.fetchall():
    print(f"  {row[0]}: {row[1]} matcher (senaste: {row[2]})")

print("\n--- Helgens matcher (maj 2026) - urval ---")
cursor.execute("""
    SELECT m.match_date, m.division,
           t1.name as team1, t2.name as team2,
           m.team1_score, m.team2_score
    FROM matches m
    JOIN teams t1 ON m.team1_id = t1.id
    JOIN teams t2 ON m.team2_id = t2.id
    WHERE season = '2025/2026'
    AND DATE(match_date) >= '2026-05-20'
    ORDER BY m.division, m.match_date
    LIMIT 30
""")
rows = cursor.fetchall()
if rows:
    for row in rows:
        print(f"  [{row[1]}] {row[0][:10]} | {row[2]} vs {row[3]} | {row[4]}-{row[5]}")
else:
    print("  Inga matcher hittades for maj 2026")

conn.close()
