#!/usr/bin/env python3
"""
Check mapping status for all first-name-only players
"""
import sqlite3

def check_first_name_mappings():
    with sqlite3.connect("goldenstat.db") as conn:
        cursor = conn.cursor()

        # Get all first-name-only players with significant matches
        cursor.execute('''
            SELECT p.id, p.name, COUNT(DISTINCT smp.sub_match_id) as match_count
            FROM players p
            JOIN sub_match_participants smp ON p.id = smp.player_id
            WHERE LENGTH(p.name) <= 15
                AND p.name NOT LIKE '% %'
                AND p.name NOT LIKE '%(%'
                AND p.name NOT LIKE '%.%'
                AND LENGTH(p.name) >= 3
            GROUP BY p.id, p.name
            HAVING match_count >= 10
            ORDER BY match_count DESC, p.name
        ''')
        first_name_players = cursor.fetchall()

        print(f"=== Checking {len(first_name_players)} first-name-only players (10+ matches) ===\n")

        has_mappings = []
        no_mappings = []

        for player_id, player_name, match_count in first_name_players:
            # Check if player has any mappings
            cursor.execute('''
                SELECT COUNT(DISTINCT correct_player_id)
                FROM sub_match_player_mappings
                WHERE original_player_id = ?
            ''', (player_id,))
            mapping_count = cursor.fetchone()[0]

            if mapping_count > 0:
                # Get mapping details
                cursor.execute('''
                    SELECT COUNT(*) as total_mappings
                    FROM sub_match_player_mappings
                    WHERE original_player_id = ?
                ''', (player_id,))
                total_mappings = cursor.fetchone()[0]

                has_mappings.append((player_name, player_id, match_count, mapping_count, total_mappings))
            else:
                no_mappings.append((player_name, player_id, match_count))

        print(f"Players WITH mappings: {len(has_mappings)}")
        for row in has_mappings[:20]:
            print(f"   {row[0]} (ID {row[1]}): {row[2]} matcher, {row[4]} mappningar till {row[3]} spelare")

        if len(has_mappings) > 20:
            print(f"   ... och {len(has_mappings) - 20} fler")

        print(f"\nPlayers WITHOUT mappings: {len(no_mappings)}")
        for row in no_mappings[:20]:
            print(f"   {row[0]} (ID {row[1]}): {row[2]} matcher")

        if len(no_mappings) > 20:
            print(f"   ... och {len(no_mappings) - 20} fler")

if __name__ == "__main__":
    check_first_name_mappings()
