#!/usr/bin/env python3
"""
Map remaining Andreas matches to Andreas (Tyresö)
"""
import sqlite3

conn = sqlite3.connect('goldenstat.db')
cursor = conn.cursor()

print("=== Mapping Andreas to Andreas (Tyresö) ===\n")

# Get unmapped Andreas matches
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
    WHERE smp.player_id = 907
    AND smp.sub_match_id NOT IN (
        SELECT sub_match_id
        FROM sub_match_player_mappings
        WHERE original_player_id = 907
    )
''')

unmapped = cursor.fetchall()

tyreso_matches = 0
other_matches = 0

for sm_id, team, season, division in unmapped:
    if 'Tyresö' in team or 'Tyresco' in team:
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
        ''', (sm_id, 907, 2184, 'Andreas (Tyresö)', context, 100, 'Club context mapping'))

        print(f"Mapped sub-match {sm_id} to Andreas (Tyresö)")
        tyreso_matches += 1
    else:
        print(f"WARNING: Sub-match {sm_id} is for {team}, not Tyresö")
        other_matches += 1

conn.commit()
print(f"\nMapped {tyreso_matches} Tyresö matches")
if other_matches:
    print(f"Skipped {other_matches} non-Tyresö matches")
