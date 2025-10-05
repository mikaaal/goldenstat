#!/usr/bin/env python3
"""
Verifiera att Petra Sweden Capital fix fungerade
"""
import sqlite3

def verify_petra_fix():
    """Verifiera Petra fix"""
    print("=== VERIFIERING AV PETRA FIX ===")

    with sqlite3.connect("goldenstat.db") as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Visa alla Petra spelare nu
        cursor.execute("SELECT id, name FROM players WHERE name LIKE 'Petra%' ORDER BY name")
        petra_players = cursor.fetchall()

        print("Alla Petra spelare efter fix:")
        for player in petra_players:
            print(f"  ID {player['id']}: {player['name']}")

        # Kontrollera Petra (Sweden Capital) specifikt
        cursor.execute("SELECT id, name FROM players WHERE name = 'Petra (Sweden Capital)'")
        sweden_petra = cursor.fetchone()

        if sweden_petra:
            print(f"\nPetra (Sweden Capital): ID {sweden_petra['id']}")

            # Kolla mappningar till denna spelare
            cursor.execute("""
                SELECT
                    COUNT(*) as mapping_count,
                    MIN(m.match_date) as first_match,
                    MAX(m.match_date) as last_match
                FROM sub_match_player_mappings smpm
                JOIN sub_matches sm ON smpm.sub_match_id = sm.id
                JOIN matches m ON sm.match_id = m.id
                WHERE smpm.correct_player_name = 'Petra (Sweden Capital)'
            """)

            mapping_info = cursor.fetchone()
            if mapping_info['mapping_count']:
                print(f"Mappningar: {mapping_info['mapping_count']} st")
                print(f"Datumspan: {mapping_info['first_match'][:10]} - {mapping_info['last_match'][:10]}")

            # Visa specifika mappningar
            cursor.execute("""
                SELECT
                    smpm.sub_match_id,
                    m.match_date,
                    CASE WHEN smp.team_number = 1 THEN t1.name ELSE t2.name END as team_name
                FROM sub_match_player_mappings smpm
                JOIN sub_matches sm ON smpm.sub_match_id = sm.id
                JOIN matches m ON sm.match_id = m.id
                JOIN teams t1 ON m.team1_id = t1.id
                JOIN teams t2 ON m.team2_id = t2.id
                JOIN sub_match_participants smp ON sm.id = smp.sub_match_id
                WHERE smpm.correct_player_name = 'Petra (Sweden Capital)'
                  AND smp.player_id = smpm.original_player_id
                ORDER BY m.match_date
            """)

            specific_mappings = cursor.fetchall()
            print(f"\nSpecifika mappningar ({len(specific_mappings)}):")
            for mapping in specific_mappings:
                print(f"  {mapping['match_date'][:10]}: {mapping['team_name']} (sub_match: {mapping['sub_match_id']})")

        else:
            print("\nINTE HITTAD: Petra (Sweden Capital)")

        # Testa en sökning som skulle simulera player search i appen
        print(f"\n=== SIMULERA PLAYER SEARCH ===")
        search_term = "petra"

        cursor.execute("""
            SELECT DISTINCT p.id, p.name, COUNT(smp.sub_match_id) as match_count
            FROM players p
            LEFT JOIN sub_match_participants smp ON p.id = smp.player_id
            LEFT JOIN sub_match_player_mappings smpm ON p.id = smpm.correct_player_id
            WHERE LOWER(p.name) LIKE LOWER(?)
            GROUP BY p.id, p.name
            ORDER BY match_count DESC, p.name
        """, (f"%{search_term}%",))

        search_results = cursor.fetchall()
        print(f"Sök på '{search_term}' ger {len(search_results)} resultat:")
        for result in search_results[:10]:  # Visa första 10
            print(f"  {result['name']}: {result['match_count']} matcher")

if __name__ == "__main__":
    verify_petra_fix()