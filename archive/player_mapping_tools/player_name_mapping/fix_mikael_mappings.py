#!/usr/bin/env python3
"""
Fix Mikael Holmström mappings - he plays for multiple clubs
"""
import sqlite3

with sqlite3.connect("goldenstat.db") as conn:
    cursor = conn.cursor()

    print("Removing incorrect mappings...")
    cursor.execute('DELETE FROM sub_match_player_mappings WHERE original_player_id = 2442')
    deleted = cursor.rowcount
    conn.commit()
    print(f"Removed {deleted} mappings\n")

    print("Creating correct club-specific mappings...")
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
        WHERE smp.player_id = 2442
    ''')

    matches = cursor.fetchall()

    for sm_id, team, season, div in matches:
        club = team.split('(')[0].strip()

        if 'Bramglaj' in club:
            target_id = 437
            target_name = 'Mikael Holmström (Bramglaj)'
        elif 'Nacka' in club or 'Wermdö' in club:
            target_id = 2359
            target_name = 'Mikael Holmström (Nacka Wermdö)'
        else:
            print(f"  WARNING: Unknown club for sub-match {sm_id}: {club}")
            continue

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
        ''', (sm_id, 2442, target_id, target_name, context, 100, 'Club-specific mapping'))

        print(f"  Sub-match {sm_id}: -> {target_name}")

    conn.commit()
    print("\nDone!")
