#!/usr/bin/env python3
"""
Debug varför bara 4 av 6 spelare importerades från Mjölner vs Dartanjang
"""
import sqlite3

def analyze_import_issue():
    """Analysera importproblemet"""
    print("=== ANALYS AV IMPORTPROBLEM ===")
    print("Förväntade spelare:")
    expected_players = [
        ("Andreas Lissbol", "Dartanjang"),
        ("Johannes Brenning", "Dartanjang"),
        ("Anders Mars", "Dartanjang"),
        ("Mats Andersson", "Dartanjang"),
        ("Micke Lundberg", "Dartanjang"),
        ("Gareth Young", "Mjölner")
    ]

    for name, team in expected_players:
        print(f"  - {name} ({team})")

    print(f"\nTotalt förväntade: {len(expected_players)} spelare")

    # Kolla vilka som faktiskt finns i databasen
    with sqlite3.connect("goldenstat.db") as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        print(f"\n=== KONTROLL AV SPELARDATABAS ===")

        for name, expected_team in expected_players:
            print(f"\nSöker: {name}")

            # Sök efter exakt namn
            cursor.execute("SELECT id, name FROM players WHERE name = ?", (name,))
            exact_matches = cursor.fetchall()

            # Sök efter varianter
            cursor.execute("SELECT id, name FROM players WHERE name LIKE ?", (f"%{name}%",))
            variant_matches = cursor.fetchall()

            if exact_matches:
                for match in exact_matches:
                    print(f"  [OK] Exakt: ID {match['id']} - {match['name']}")

                    # Kolla om denna spelare spelade 2025-09-23
                    cursor.execute("""
                        SELECT COUNT(*) as match_count
                        FROM sub_match_participants smp
                        JOIN sub_matches sm ON smp.sub_match_id = sm.id
                        JOIN matches m ON sm.match_id = m.id
                        WHERE smp.player_id = ? AND DATE(m.match_date) = '2025-09-23'
                    """, (match['id'],))

                    date_matches = cursor.fetchone()['match_count']
                    if date_matches > 0:
                        print(f"    -> SPELADE 2025-09-23: {date_matches} matcher")
                    else:
                        print(f"    -> Spelade INTE 2025-09-23")

            elif variant_matches:
                print(f"  ~ Varianter hittades:")
                for match in variant_matches:
                    print(f"    ID {match['id']} - {match['name']}")

                    # Kolla om denna variant spelade 2025-09-23
                    cursor.execute("""
                        SELECT COUNT(*) as match_count
                        FROM sub_match_participants smp
                        JOIN sub_matches sm ON smp.sub_match_id = sm.id
                        JOIN matches m ON sm.match_id = m.id
                        WHERE smp.player_id = ? AND DATE(m.match_date) = '2025-09-23'
                    """, (match['id'],))

                    date_matches = cursor.fetchone()['match_count']
                    if date_matches > 0:
                        print(f"    -> SPELADE 2025-09-23: {date_matches} matcher")
            else:
                print(f"  [NOT FOUND] INTE HITTAD: {name}")

        # Sammanfattning av vad som faktiskt importerades 2025-09-23
        print(f"\n=== VID IMPORTERADES 2025-09-23 ===")
        cursor.execute("""
            SELECT DISTINCT p.name,
                   CASE WHEN smp.team_number = 1 THEN t1.name ELSE t2.name END as team_name
            FROM sub_match_participants smp
            JOIN sub_matches sm ON smp.sub_match_id = sm.id
            JOIN matches m ON sm.match_id = m.id
            JOIN players p ON smp.player_id = p.id
            JOIN teams t1 ON m.team1_id = t1.id
            JOIN teams t2 ON m.team2_id = t2.id
            WHERE DATE(m.match_date) = '2025-09-23'
            ORDER BY team_name, p.name
        """)

        imported_players = cursor.fetchall()
        print(f"Faktiskt importerade spelare ({len(imported_players)}):")
        for player in imported_players:
            print(f"  [OK] {player['name']} ({player['team_name']})")

        # Identifiera saknade spelare
        imported_names = [p['name'] for p in imported_players]
        expected_names = [name for name, _ in expected_players]

        missing_players = []
        for expected_name in expected_names:
            found = False
            for imported_name in imported_names:
                if expected_name.lower() in imported_name.lower():
                    found = True
                    break
            if not found:
                missing_players.append(expected_name)

        if missing_players:
            print(f"\n[MISSING] SAKNADE SPELARE ({len(missing_players)}):")
            for missing in missing_players:
                print(f"  - {missing}")
        else:
            print(f"\n[OK] Alla spelare hittades (men kanske med varianta namn)")

if __name__ == "__main__":
    analyze_import_issue()