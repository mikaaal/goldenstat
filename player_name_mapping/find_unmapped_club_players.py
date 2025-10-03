#!/usr/bin/env python3
"""
Find generic player names that have matches but no mappings,
where club-specific versions of the player already exist.
"""
import sqlite3

def find_unmapped_club_players():
    with sqlite3.connect("goldenstat.db") as conn:
        cursor = conn.cursor()

        print("=== Finding unmapped generic players with club-specific versions ===\n")

        # Find all generic player names (no parentheses, no special chars)
        cursor.execute('''
            SELECT DISTINCT p.id, p.name, COUNT(DISTINCT smp.sub_match_id) as match_count
            FROM players p
            JOIN sub_match_participants smp ON p.id = smp.player_id
            WHERE p.name NOT LIKE '%(%'
                AND LENGTH(p.name) >= 3
            GROUP BY p.id, p.name
            HAVING match_count >= 1
            ORDER BY match_count DESC
        ''')

        generic_players = cursor.fetchall()

        unmapped_with_club_versions = []

        for player_id, player_name, match_count in generic_players:
            # Check if this player has any mappings
            cursor.execute('''
                SELECT COUNT(*)
                FROM sub_match_player_mappings
                WHERE original_player_id = ?
            ''', (player_id,))

            has_mappings = cursor.fetchone()[0] > 0

            if has_mappings:
                continue  # Already mapped, skip

            # Check if club-specific versions exist
            cursor.execute('''
                SELECT id, name
                FROM players
                WHERE name LIKE ? || ' (%'
                ORDER BY name
            ''', (player_name,))

            club_versions = cursor.fetchall()

            if club_versions:
                # Get which clubs this generic player has played for
                cursor.execute('''
                    SELECT DISTINCT
                        CASE WHEN smp.team_number = 1 THEN t1.name ELSE t2.name END as team
                    FROM sub_match_participants smp
                    JOIN sub_matches sm ON smp.sub_match_id = sm.id
                    JOIN matches m ON sm.match_id = m.id
                    JOIN teams t1 ON m.team1_id = t1.id
                    JOIN teams t2 ON m.team2_id = t2.id
                    WHERE smp.player_id = ?
                ''', (player_id,))

                teams = [row[0] for row in cursor.fetchall()]

                unmapped_with_club_versions.append({
                    'id': player_id,
                    'name': player_name,
                    'match_count': match_count,
                    'club_versions': club_versions,
                    'teams': teams
                })

        if unmapped_with_club_versions:
            print(f"Found {len(unmapped_with_club_versions)} generic players with club versions:\n")

            for item in unmapped_with_club_versions[:20]:
                print(f"{item['name']} (ID {item['id']}, {item['match_count']} matches)")
                print(f"  Club versions exist:")
                for cv_id, cv_name in item['club_versions']:
                    print(f"    - {cv_name} (ID {cv_id})")
                print(f"  Played for: {', '.join([t.split('(')[0].strip() for t in item['teams'][:3]])}")
                print()

            if len(unmapped_with_club_versions) > 20:
                print(f"... and {len(unmapped_with_club_versions) - 20} more")
        else:
            print("No unmapped generic players with club versions found!")

if __name__ == "__main__":
    find_unmapped_club_players()
