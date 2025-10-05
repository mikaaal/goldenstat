#!/usr/bin/env python3
"""
Automatically map all unmapped Nacka Wermdö matches
"""
import sqlite3

def auto_map_nacka_players(dry_run=True):
    conn = sqlite3.connect('goldenstat.db')
    cursor = conn.cursor()

    # Get all players with (Nacka Wermdö) in their name
    cursor.execute('SELECT id, name FROM players WHERE name LIKE "%(Nacka Wermdö)%"')
    nacka_players = cursor.fetchall()

    print(f"=== Auto-mapping Nacka Wermdö players ===\n")

    total_mapped = 0

    for target_id, target_name in nacka_players:
        # Get base name (without club)
        base_name = target_name.split(' (')[0]

        # Find base player
        cursor.execute('SELECT id FROM players WHERE name = ?', (base_name,))
        base_result = cursor.fetchone()

        if not base_result:
            continue

        base_id = base_result[0]

        # Get unmapped matches
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
            WHERE smp.player_id = ?
            AND smp.sub_match_id NOT IN (
                SELECT sub_match_id
                FROM sub_match_player_mappings
                WHERE original_player_id = ?
            )
        ''', (base_id, base_id))

        unmapped_matches = cursor.fetchall()

        mapped_count = 0

        for sm_id, team, season, division in unmapped_matches:
            # Only map if it's a Nacka Wermdö match
            if 'Nacka' in team and 'Wermdö' in team:
                context = f'{team} ({division}) {season}'

                if not dry_run:
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
                    ''', (sm_id, base_id, target_id, target_name, context, 100, 'Auto-mapped Nacka Wermdö'))

                mapped_count += 1
                total_mapped += 1

        if mapped_count > 0:
            if dry_run:
                print(f"[DRY RUN] Would map {base_name} -> {target_name}: {mapped_count} matches")
            else:
                print(f"Mapped {base_name} -> {target_name}: {mapped_count} matches")

    if not dry_run:
        conn.commit()
        print(f"\n=== COMPLETED ===")
        print(f"Created {total_mapped} new mappings")
    else:
        print(f"\n=== DRY RUN ===")
        print(f"Would create {total_mapped} new mappings")
        print("\nRun with --apply to create mappings")

    conn.close()

if __name__ == "__main__":
    import sys
    if "--apply" in sys.argv:
        auto_map_nacka_players(dry_run=False)
    else:
        auto_map_nacka_players(dry_run=True)
