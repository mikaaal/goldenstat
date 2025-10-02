#!/usr/bin/env python3
"""
Find all Nacka Wermdö players with unmapped matches
"""
import sqlite3

conn = sqlite3.connect('goldenstat.db')
cursor = conn.cursor()

# Get all players with (Nacka Wermdö) in their name
cursor.execute('SELECT id, name FROM players WHERE name LIKE "%(Nacka Wermdö)%"')
nacka_players = cursor.fetchall()

print(f"=== Checking {len(nacka_players)} Nacka Wermdö players ===\n")

unmapped_found = []

for target_id, target_name in nacka_players:
    # Get base name (without club)
    base_name = target_name.split(' (')[0]

    # Find base player
    cursor.execute('SELECT id FROM players WHERE name = ?', (base_name,))
    base_result = cursor.fetchone()

    if not base_result:
        continue

    base_id = base_result[0]

    # Check if base player has any unmapped matches
    cursor.execute('''
        SELECT smp.sub_match_id
        FROM sub_match_participants smp
        WHERE smp.player_id = ?
        AND smp.sub_match_id NOT IN (
            SELECT sub_match_id
            FROM sub_match_player_mappings
            WHERE original_player_id = ?
        )
    ''', (base_id, base_id))

    unmapped_matches = cursor.fetchall()

    if unmapped_matches:
        # Verify these are Nacka Wermdö matches
        nacka_matches = []
        for (sm_id,) in unmapped_matches:
            cursor.execute('''
                SELECT
                    CASE WHEN smp.team_number = 1 THEN t1.name ELSE t2.name END as team
                FROM sub_match_participants smp
                JOIN sub_matches sm ON smp.sub_match_id = sm.id
                JOIN matches m ON sm.match_id = m.id
                JOIN teams t1 ON m.team1_id = t1.id
                JOIN teams t2 ON m.team2_id = t2.id
                WHERE smp.sub_match_id = ? AND smp.player_id = ?
            ''', (sm_id, base_id))

            team = cursor.fetchone()[0]
            if 'Nacka' in team and 'Wermdö' in team:
                nacka_matches.append(sm_id)

        if nacka_matches:
            unmapped_found.append({
                'base_id': base_id,
                'base_name': base_name,
                'target_id': target_id,
                'target_name': target_name,
                'unmapped_count': len(nacka_matches),
                'sub_match_ids': nacka_matches
            })
            print(f"{base_name} -> {target_name}")
            print(f"  {len(nacka_matches)} unmapped Nacka Wermdö matches")
            print()

if unmapped_found:
    print(f"\n=== Found {len(unmapped_found)} players with unmapped Nacka Wermdö matches ===")
    print(f"Total unmapped matches: {sum(p['unmapped_count'] for p in unmapped_found)}")
else:
    print("All Nacka Wermdö players are correctly mapped!")
