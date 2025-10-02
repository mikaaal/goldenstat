#!/usr/bin/env python3
import sqlite3

conn = sqlite3.connect('goldenstat.db')
cursor = conn.cursor()

unmapped = [10135, 10137, 18684, 18685, 19281, 19282]

for sm_id in unmapped:
    cursor.execute('''
        SELECT
            CASE WHEN smp.team_number = 1 THEN t1.name ELSE t2.name END,
            m.season,
            m.division
        FROM sub_match_participants smp
        JOIN sub_matches sm ON smp.sub_match_id = sm.id
        JOIN matches m ON sm.match_id = m.id
        JOIN teams t1 ON m.team1_id = t1.id
        JOIN teams t2 ON m.team2_id = t2.id
        WHERE smp.sub_match_id = ? AND smp.player_id = 1333
    ''', (sm_id,))

    team, season, div = cursor.fetchone()
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
    ''', (sm_id, 1333, 2201, 'Wetter (Nacka Wermdö)', context, 100, 'Club context mapping'))

    print(f'Mapped sub-match {sm_id}')

conn.commit()
print('Done!')
