#!/usr/bin/env python3
"""
Check mapping status for all Nacka Wermdö contextual players
"""
import sqlite3

def check_nacka_mappings():
    with sqlite3.connect("goldenstat.db") as conn:
        cursor = conn.cursor()

        # Get all contextual Nacka Wermdö players
        cursor.execute('SELECT id, name FROM players WHERE name LIKE "%(Nacka Wermdö)%" ORDER BY name')
        contextual = cursor.fetchall()

        print(f"=== Checking {len(contextual)} Nacka Wermdö players ===\n")

        missing_mappings = []
        has_mappings = []

        for ctx_id, ctx_name in contextual:
            base_name = ctx_name.split(' (')[0]

            # Check if base name exists
            cursor.execute('SELECT id FROM players WHERE name = ?', (base_name,))
            base = cursor.fetchone()

            if base:
                base_id = base[0]

                # Check if mapping exists
                cursor.execute('''
                    SELECT COUNT(*)
                    FROM sub_match_player_mappings
                    WHERE original_player_id = ? AND correct_player_id = ?
                ''', (base_id, ctx_id))
                mapping_count = cursor.fetchone()[0]

                if mapping_count > 0:
                    has_mappings.append((base_name, base_id, ctx_name, ctx_id, mapping_count))
                else:
                    # Check if base player has any matches
                    cursor.execute('''
                        SELECT COUNT(*)
                        FROM sub_match_participants
                        WHERE player_id = ?
                    ''', (base_id,))
                    base_match_count = cursor.fetchone()[0]

                    missing_mappings.append((base_name, base_id, ctx_name, ctx_id, base_match_count))
            else:
                print(f"WARNING: Base player '{base_name}' does not exist for {ctx_name}")

        print(f"Players WITH mappings: {len(has_mappings)}")
        for row in has_mappings:
            print(f"   {row[0]} (ID {row[1]}) -> {row[2]} (ID {row[3]}): {row[4]} mappningar")

        print(f"\nPlayers WITHOUT mappings: {len(missing_mappings)}")
        for row in missing_mappings:
            print(f"   {row[0]} (ID {row[1]}) -> {row[2]} (ID {row[3]}): base har {row[4]} matcher")

if __name__ == "__main__":
    check_nacka_mappings()
