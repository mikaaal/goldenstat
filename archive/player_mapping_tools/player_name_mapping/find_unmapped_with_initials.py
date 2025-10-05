#!/usr/bin/env python3
"""
Find players with initials (like "Richard G") that should be mapped to club versions
"""
import sqlite3

conn = sqlite3.connect('goldenstat.db')
cursor = conn.cursor()

# Find players with pattern "Name X" where X is a single letter or initial
cursor.execute('''
    SELECT DISTINCT p.id, p.name
    FROM players p
    JOIN sub_match_participants smp ON p.id = smp.player_id
    WHERE p.name LIKE '% _'
       OR p.name LIKE '% _.'
    AND NOT EXISTS (
        SELECT 1 FROM sub_match_player_mappings WHERE original_player_id = p.id
    )
''')

initial_players = cursor.fetchall()

print(f"=== Found {len(initial_players)} players with initials ===\n")

for player_id, player_name in initial_players:
    # Get teams they play for
    cursor.execute('''
        SELECT DISTINCT
            CASE WHEN smp.team_number = 1 THEN t1.name ELSE t2.name END as team,
            COUNT(*) as match_count
        FROM sub_match_participants smp
        JOIN sub_matches sm ON smp.sub_match_id = sm.id
        JOIN matches m ON sm.match_id = m.id
        JOIN teams t1 ON m.team1_id = t1.id
        JOIN teams t2 ON m.team2_id = t2.id
        WHERE smp.player_id = ?
        GROUP BY team
    ''', (player_id,))

    teams = cursor.fetchall()

    # Check if there's a club-specific version
    first_name = player_name.split()[0]
    cursor.execute('''
        SELECT id, name
        FROM players
        WHERE name LIKE ? || ' %(%'
    ''', (first_name,))

    club_versions = cursor.fetchall()

    if teams:
        print(f"{player_name} (ID {player_id})")
        for team, count in teams:
            club = team.split('(')[0].strip()
            print(f"  Plays for {club}: {count} matches")

        if club_versions:
            print(f"  Club versions exist:")
            for cv_id, cv_name in club_versions:
                print(f"    - {cv_name} (ID {cv_id})")
        print()

conn.close()
