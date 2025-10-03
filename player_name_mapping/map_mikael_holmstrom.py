#!/usr/bin/env python3
"""
Map Mikael Holmström to Mikael Holmström (Nacka Wermdö)
"""
import sqlite3

def map_mikael_holmstrom():
    with sqlite3.connect("../goldenstat.db") as conn:
        cursor = conn.cursor()

        # Get player IDs
        cursor.execute("SELECT id, name FROM players WHERE name LIKE '%Mikael Holmström%' OR name LIKE '%Mikael Holmstr_m%'")
        players = cursor.fetchall()

        print("=== MIKAEL HOLMSTRÖM MAPPING ===\n")
        print("Found players:")
        for p_id, name in players:
            print(f"  ID {p_id}: {name}")

        # Find base and target
        base_id = None
        target_id = None

        for p_id, name in players:
            if name == "Mikael Holmström":
                base_id = p_id
            elif "Nacka" in name and "Wermdö" in name:
                target_id = p_id

        if not base_id:
            print("\nNo base 'Mikael Holmström' player found - nothing to map")
            return

        if not target_id:
            print("\nWARNING: 'Mikael Holmström (Nacka Wermdö)' not found")
            # Create it
            cursor.execute("INSERT INTO players (name) VALUES (?)", ("Mikael Holmström (Nacka Wermdö)",))
            target_id = cursor.lastrowid
            conn.commit()
            print(f"Created Mikael Holmström (Nacka Wermdö) with ID: {target_id}")

        print(f"\nMapping: Mikael Holmström (ID {base_id}) -> Mikael Holmström (Nacka Wermdö) (ID {target_id})")

        # Get all sub-matches for base player
        cursor.execute('''
            SELECT DISTINCT
                smp.sub_match_id,
                CASE WHEN smp.team_number = 1 THEN t1.name ELSE t2.name END as team_name,
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

        sub_matches = cursor.fetchall()

        print(f"Found {len(sub_matches)} sub-matches to map\n")

        if sub_matches:
            for sm_id, team, season, division in sub_matches:
                context = f"{team} ({division}) {season}"
                print(f"  Sub-match {sm_id}: {context}")

                cursor.execute('''
                    INSERT OR REPLACE INTO sub_match_player_mappings (
                        sub_match_id,
                        original_player_id,
                        correct_player_id,
                        correct_player_name,
                        match_context,
                        confidence,
                        mapping_reason,
                        notes
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    sm_id,
                    base_id,
                    target_id,
                    "Mikael Holmström (Nacka Wermdö)",
                    context,
                    100,
                    "Club context mapping - all matches from Nacka Wermdö",
                    "Manual mapping for Mikael Holmström"
                ))

            conn.commit()
            print(f"\nCreated {len(sub_matches)} mappings")
        else:
            print("No new mappings needed")

if __name__ == "__main__":
    map_mikael_holmstrom()
