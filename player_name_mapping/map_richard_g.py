#!/usr/bin/env python3
import sqlite3

conn = sqlite3.connect('goldenstat.db')
cursor = conn.cursor()

# Get all Richard G matches
cursor.execute('''
    SELECT
        smp.sub_match_id,
        CASE WHEN smp.team_number = 1 THEN t1.name ELSE t2.name END,
        m.season,
        m.division
    FROM sub_match_participants smp
    JOIN sub_matches sm ON smp.sub_match_id = sm.id
    JOIN matches m ON sm.match_id = m.id
    JOIN teams t1 ON m.team1_id = t1.id
    JOIN teams t2 ON m.team2_id = t2.id
    WHERE smp.player_id = 329
''')

matches = cursor.fetchall()

for sm_id, team, season, div in matches:
    context = f'{team} ({div}) {season}'

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
    ''', (sm_id, 329, 2173, 'Richard (Nacka Wermdö)', context, 100, 'Club context mapping - Richard G to Richard'))

    print(f'Mapped sub-match {sm_id}')

conn.commit()
print(f'Done! Mapped {len(matches)} matches')
