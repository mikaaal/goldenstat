#!/usr/bin/env python3
"""
Debug Johan Brink duplicates in player search
"""
import sqlite3

def debug_johan_brink_duplicates():
    """Debug why there are still two Johan Brink entries"""
    print("=== DEBUGGING JOHAN BRINK DUPLICATES ===")

    with sqlite3.connect("goldenstat.db") as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Check all Johan Brink players in database
        print("1. All Johan Brink variations in players table:")
        cursor.execute("SELECT id, name FROM players WHERE name LIKE 'Johan%rink%'")
        johan_players = cursor.fetchall()

        for player in johan_players:
            print(f"   ID: {player['id']}, Name: '{player['name']}'")

        # Check mappings
        print("\n2. Johan Brink mappings:")
        cursor.execute("""
            SELECT original_player_id, correct_player_id, correct_player_name
            FROM sub_match_player_mappings
            WHERE correct_player_name LIKE 'Johan%rink%'
            OR original_player_id IN (SELECT id FROM players WHERE name LIKE 'Johan%rink%')
        """)
        mappings = cursor.fetchall()

        for mapping in mappings:
            print(f"   {mapping['original_player_id']} -> {mapping['correct_player_id']}: '{mapping['correct_player_name']}'")

        # Run the actual API query to see what gets returned
        print("\n3. Current API query results:")
        cursor.execute("""
            SELECT
                p.name,
                COUNT(DISTINCT smp.sub_match_id) as total_matches,
                'direct' as source
            FROM players p
            JOIN sub_match_participants smp ON p.id = smp.player_id
            JOIN sub_matches sm ON smp.sub_match_id = sm.id
            JOIN matches m ON sm.match_id = m.id
            WHERE p.id NOT IN (
                SELECT DISTINCT original_player_id
                FROM sub_match_player_mappings
            )
            AND p.name LIKE 'Johan%rink%'
            GROUP BY p.id, p.name
            HAVING COUNT(DISTINCT smp.sub_match_id) >= 3

            UNION

            -- Include contextual players that exist only through mappings
            SELECT
                smpm.correct_player_name as name,
                COUNT(DISTINCT smpm.sub_match_id) as total_matches,
                'mapped' as source
            FROM sub_match_player_mappings smpm
            WHERE smpm.correct_player_name LIKE 'Johan%rink%'
            GROUP BY smpm.correct_player_name
            HAVING COUNT(DISTINCT smpm.sub_match_id) >= 3

            ORDER BY name
        """)

        api_results = cursor.fetchall()
        print("   API query returns:")
        for result in api_results:
            print(f"     '{result['name']}' ({result['total_matches']} matches, source: {result['source']})")

if __name__ == "__main__":
    debug_johan_brink_duplicates()