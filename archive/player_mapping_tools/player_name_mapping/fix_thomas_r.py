#!/usr/bin/env python3
"""
Fix Thomas R mappings - should map TO a proper player, not FROM
"""
import sqlite3

conn = sqlite3.connect('goldenstat.db')
cursor = conn.cursor()

print("=== Fixing Thomas R mappings ===\n")

# 1. Delete incorrect mappings where Thomas -> Thomas R
cursor.execute('''
    DELETE FROM sub_match_player_mappings
    WHERE original_player_id = 899 AND correct_player_id = 1262
''')
deleted = cursor.rowcount
print(f"1. Deleted {deleted} incorrect mappings (Thomas -> Thomas R)")

# 2. Check if Thomas (Tyresö DC) exists
cursor.execute('SELECT id FROM players WHERE name = "Thomas (Tyresö DC)"')
result = cursor.fetchone()

if result:
    thomas_dc_id = result[0]
    print(f"2. Thomas (Tyresö DC) exists with ID {thomas_dc_id}")
else:
    # Create Thomas (Tyresö DC)
    cursor.execute('INSERT INTO players (name) VALUES (?)', ('Thomas (Tyresö DC)',))
    thomas_dc_id = cursor.lastrowid
    print(f"2. Created Thomas (Tyresö DC) with ID {thomas_dc_id}")

# 3. Create mappings from Thomas R -> Thomas (Tyresö DC)
cursor.execute('''
    SELECT
        smp.sub_match_id,
        CASE WHEN smp.team_number = 1 THEN t1.name ELSE t2.name END as team,
        m.season,
        m.division
    FROM sub_match_participants smp
    JOIN sub_matches sm ON smp.sub_match_id = sm.id
    JOIN matches m ON sm.match_id = m.id
    JOIN teams t1 ON m.team1_id = t1.id
    JOIN teams t2 ON m.team2_id = t2.id
    WHERE smp.player_id = 1262
''')

matches = cursor.fetchall()

for sm_id, team, season, division in matches:
    context = f'{team} ({division}) {season}'

    cursor.execute('''
        INSERT INTO sub_match_player_mappings (
            sub_match_id,
            original_player_id,
            correct_player_id,
            correct_player_name,
            match_context,
            confidence,
            mapping_reason
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (sm_id, 1262, thomas_dc_id, 'Thomas (Tyresö DC)', context, 100, 'Club context mapping - Thomas R to Thomas'))

print(f"3. Created {len(matches)} mappings (Thomas R -> Thomas (Tyresö DC))")

conn.commit()
print("\nDone!")
