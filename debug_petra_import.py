#!/usr/bin/env python3
"""
Debug vad som hände med Petra under 2FB importen
"""
import sqlite3

def debug_petra_import():
    """Undersök Petra-importen"""
    print("=== DEBUG PETRA IMPORT ===")

    with sqlite3.connect("goldenstat.db") as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Leta efter Petra spelare
        print("Alla Petra spelare i databasen:")
        cursor.execute("SELECT id, name FROM players WHERE name LIKE 'Petra%' ORDER BY name")
        petra_players = cursor.fetchall()

        for player in petra_players:
            print(f"  ID {player['id']}: {player['name']}")

        # Kolla om det finns en bara-förnamn Petra
        cursor.execute("SELECT id, name FROM players WHERE name = 'Petra'")
        petra_first_name = cursor.fetchone()

        if petra_first_name:
            print(f"\nPetra (förnamn) spelare: ID {petra_first_name['id']}")

            # Kolla vilka matcher denna Petra spelat
            cursor.execute("""
                SELECT
                    sm.id as sub_match_id,
                    m.match_date,
                    CASE WHEN smp.team_number = 1 THEN t1.name ELSE t2.name END as team_name,
                    m.division
                FROM sub_match_participants smp
                JOIN sub_matches sm ON smp.sub_match_id = sm.id
                JOIN matches m ON sm.match_id = m.id
                JOIN teams t1 ON m.team1_id = t1.id
                JOIN teams t2 ON m.team2_id = t2.id
                WHERE smp.player_id = ?
                ORDER BY m.match_date DESC
            """, (petra_first_name['id'],))

            petra_matches = cursor.fetchall()
            print(f"Petra (förnamn) har spelat {len(petra_matches)} matcher:")

            # Gruppera per lag
            teams = {}
            for match in petra_matches:
                team = match['team_name']
                if team not in teams:
                    teams[team] = []
                teams[team].append(match)

            for team, matches in teams.items():
                print(f"  {team}: {len(matches)} matcher")
                for match in matches[:3]:  # Visa första 3
                    print(f"    {match['match_date'][:10]} (sub_match: {match['sub_match_id']})")
                if len(matches) > 3:
                    print(f"    ... och {len(matches) - 3} till")

            # Kolla om det finns mappningar för Petra
            cursor.execute("""
                SELECT COUNT(*) as mapping_count
                FROM sub_match_player_mappings
                WHERE original_player_id = ?
            """, (petra_first_name['id'],))

            mapping_count = cursor.fetchone()['mapping_count']
            print(f"\nBefintliga mappningar för Petra: {mapping_count}")

        else:
            print("\nIngen 'Petra' (förnamn-endast) spelare hittad")

        # Kolla om det finns Sweden Capital i team-namnet
        print(f"\n=== SWEDEN CAPITAL KONTEXT ===")
        cursor.execute("""
            SELECT DISTINCT t.name
            FROM teams t
            WHERE t.name LIKE '%Sweden%Capital%' OR t.name LIKE '%capital%'
        """)

        capital_teams = cursor.fetchall()
        if capital_teams:
            print("Sweden Capital relaterade lag:")
            for team in capital_teams:
                print(f"  {team['name']}")
        else:
            print("Inga Sweden Capital lag hittade")

        # Kolla 2FB divisionens lag
        print(f"\n=== 2FB DIVISION LAG ===")
        cursor.execute("""
            SELECT DISTINCT t.name
            FROM teams t
            JOIN matches m ON t.id = m.team1_id OR t.id = m.team2_id
            WHERE m.division = '2FB'
            ORDER BY t.name
        """)

        division_teams = cursor.fetchall()
        print(f"Lag i 2FB divisionen ({len(division_teams)}):")
        for team in division_teams:
            print(f"  {team['name']}")

if __name__ == "__main__":
    debug_petra_import()