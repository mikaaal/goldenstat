#!/usr/bin/env python3
"""Fix team_games flag for existing tournaments.

Detects doubles tournaments by checking if any participant has more than one
player linked (via participant_players), and sets team_games = 1.
"""
import sqlite3

DB_PATH = "cups.db"

conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row

# Find tournaments where team_games=0 but participants have >1 player
rows = conn.execute("""
    SELECT t.id, t.title
    FROM tournaments t
    WHERE t.team_games = 0
      AND (SELECT MAX(cnt) FROM (
          SELECT COUNT(*) as cnt FROM participant_players pp
          JOIN participants p ON pp.participant_id = p.id
          WHERE p.tournament_id = t.id GROUP BY pp.participant_id
      )) > 1
""").fetchall()

if not rows:
    print("No tournaments to fix.")
else:
    ids = [r['id'] for r in rows]
    conn.execute(
        f"UPDATE tournaments SET team_games = 1 WHERE id IN ({','.join('?' * len(ids))})",
        ids,
    )
    conn.commit()
    print(f"Updated {len(ids)} tournaments to team_games=1:")
    for r in rows:
        print(f"  [{r['id']}] {r['title']}")

conn.close()
