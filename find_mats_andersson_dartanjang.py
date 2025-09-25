#!/usr/bin/env python3
"""
Leta efter Mats Andersson (Dartanjang) som borde ha hittats
"""
import sqlite3

def find_mats_andersson_dartanjang():
    """Leta efter Mats Andersson (Dartanjang) spelare"""
    print("=== LETA EFTER MATS ANDERSSON (DARTANJANG) ===")

    with sqlite3.connect("goldenstat.db") as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Sök efter alla Mats Andersson varianter
        print("Alla Mats Andersson spelare:")
        cursor.execute("SELECT id, name FROM players WHERE name LIKE 'Mats Andersson%' ORDER BY name")
        mats_andersons = cursor.fetchall()

        for player in mats_andersons:
            print(f"  ID {player['id']}: {player['name']}")

        # Sök specifikt efter Mats Andersson (Dartanjang)
        print(f"\nSöker specifikt 'Mats Andersson (Dartanjang)':")
        cursor.execute("SELECT id, name FROM players WHERE name = 'Mats Andersson (Dartanjang)'")
        dartanjang_mats = cursor.fetchone()

        if dartanjang_mats:
            print(f"  [FOUND] ID {dartanjang_mats['id']}: {dartanjang_mats['name']}")

            # Kolla om denna spelare har några mappningar
            cursor.execute("""
                SELECT COUNT(*) as mapping_count
                FROM sub_match_player_mappings smpm
                WHERE smpm.correct_player_id = ?
            """, (dartanjang_mats['id'],))

            mapping_count = cursor.fetchone()['mapping_count']
            print(f"  Antal mappningar till denna spelare: {mapping_count}")

            # Kolla om denna spelare har spelat några matcher
            cursor.execute("""
                SELECT COUNT(*) as match_count
                FROM sub_match_participants smp
                WHERE smp.player_id = ?
            """, (dartanjang_mats['id'],))

            match_count = cursor.fetchone()['match_count']
            print(f"  Antal matcher spelad: {match_count}")

        else:
            print(f"  [NOT FOUND] Mats Andersson (Dartanjang) finns INTE!")

            # Kolla om det finns separerade Mats spelare
            print(f"\nAlla separerade Mats spelare:")
            cursor.execute("SELECT id, name FROM players WHERE name LIKE 'Mats %(%' ORDER BY name")
            separated_mats = cursor.fetchall()

            for player in separated_mats:
                print(f"  ID {player['id']}: {player['name']}")

        # Kolla också alla mappningar där source är "Mats" och target innehåller "Dartanjang"
        print(f"\nMappningar från 'Mats' till Dartanjang-relaterade spelare:")
        cursor.execute("""
            SELECT DISTINCT smpm.correct_player_name, COUNT(*) as count
            FROM sub_match_player_mappings smpm
            JOIN players p ON smpm.original_player_id = p.id
            WHERE p.name = 'Mats'
              AND smpm.correct_player_name LIKE '%Dartanjang%'
            GROUP BY smpm.correct_player_name
            ORDER BY count DESC
        """)

        dartanjang_mappings = cursor.fetchall()
        if dartanjang_mappings:
            for mapping in dartanjang_mappings:
                print(f"  Mats -> {mapping['correct_player_name']} ({mapping['count']}x)")
        else:
            print(f"  Inga mappningar till Dartanjang-spelare hittades")

if __name__ == "__main__":
    find_mats_andersson_dartanjang()