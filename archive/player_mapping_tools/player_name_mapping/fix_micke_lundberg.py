#!/usr/bin/env python3
"""
Fix Micke Lundberg - Split one player into multiple based on club affiliation
Based on fix_mats_andersson.py template

Micke Lundberg (SpikKastarna) ID: 1235 currently has:
- 14 matcher för SpikKastarna
- 2 matcher för Spikkastarna (samma klubb)
- 3 matcher för Dartanjang (2A)

Should become:
- Micke Lundberg (Spikkastarna) - 16 matcher (SpikKastarna + Spikkastarna)
- Micke Lundberg (Dartanjang) - 3 matcher (Dartanjang 2A)
"""
import sqlite3
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def analyze_current_situation():
    """Analyze current Micke Lundberg situation"""
    print("=== ANALYS AV NUVARANDE SITUATION ===")

    with sqlite3.connect("../goldenstat.db") as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Visa nuvarande spelare
        cursor.execute("SELECT id, name FROM players WHERE name LIKE 'Micke Lundberg%'")
        players = cursor.fetchall()

        print("Nuvarande Micke Lundberg spelare:")
        for player in players:
            print(f"  ID {player['id']}: {player['name']}")

        # Analysera matcher per klubb för ID 1235
        if players:
            print(f"\nMatcher per klubb för {players[0]['name']} (ID {players[0]['id']}):")
            cursor.execute("""
                SELECT
                    CASE WHEN smp.team_number = 1 THEN t1.name ELSE t2.name END as player_team,
                    COUNT(*) as match_count
                FROM sub_match_participants smp
                JOIN sub_matches sm ON smp.sub_match_id = sm.id
                JOIN matches m ON sm.match_id = m.id
                JOIN teams t1 ON m.team1_id = t1.id
                JOIN teams t2 ON m.team2_id = t2.id
                WHERE smp.player_id = ?
                GROUP BY player_team
                ORDER BY match_count DESC
            """, (players[0]['id'],))

            club_stats = cursor.fetchall()
            for stat in club_stats:
                print(f"    {stat['player_team']}: {stat['match_count']} matcher")

        return players

def create_new_players():
    """Create new player entry for Dartanjang"""
    print("\n=== SKAPAR NY SPELARE ===")

    with sqlite3.connect("../goldenstat.db") as conn:
        cursor = conn.cursor()

        # Skapa 1 ny spelare (vi behåller ID 1235 för Spikkastarna, byter namn)
        new_player_name = "Micke Lundberg (Dartanjang)"

        cursor.execute("INSERT INTO players (name) VALUES (?)", (new_player_name,))
        dartanjang_id = cursor.lastrowid
        print(f"Skapade: ID {dartanjang_id} - {new_player_name}")

        conn.commit()
        return dartanjang_id

def update_player_assignments(dartanjang_id):
    """Update sub_match_participants with correct player IDs"""
    print("\n=== UPPDATERAR SPELARE-TILLDELNINGAR ===")

    with sqlite3.connect("../goldenstat.db") as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Flytta Dartanjang matcher till ny spelare
        cursor.execute("""
            UPDATE sub_match_participants
            SET player_id = ?
            WHERE player_id = 1235
            AND sub_match_id IN (
                SELECT sm.id
                FROM sub_matches sm
                JOIN matches m ON sm.match_id = m.id
                JOIN teams t1 ON m.team1_id = t1.id
                JOIN teams t2 ON m.team2_id = t2.id
                WHERE (
                    (sub_match_participants.team_number = 1 AND t1.name LIKE 'Dartanjang%') OR
                    (sub_match_participants.team_number = 2 AND t2.name LIKE 'Dartanjang%')
                )
            )
        """, (dartanjang_id,))
        dartanjang_updated = cursor.rowcount
        print(f"Flyttade {dartanjang_updated} Dartanjang matcher till ny spelare (ID {dartanjang_id})")

        # Uppdatera originalspelaren till Spikkastarna (slå ihop SpikKastarna + Spikkastarna)
        cursor.execute("UPDATE players SET name = 'Micke Lundberg (Spikkastarna)' WHERE id = 1235")
        print("Uppdaterade original spelare (1235) till 'Micke Lundberg (Spikkastarna)'")

        # Ta bort tomma spelaren ID 2351 om den inte har några matcher
        cursor.execute("SELECT COUNT(*) FROM sub_match_participants WHERE player_id = 2351")
        count_2351 = cursor.fetchone()[0]
        if count_2351 == 0:
            cursor.execute("DELETE FROM players WHERE id = 2351")
            print("Tog bort tom spelare 'Micke Lundberg (Spikkastarna)' ID 2351")
        else:
            print(f"Behåller spelare ID 2351, har {count_2351} matcher")

        conn.commit()

def verify_results():
    """Verify the results of the split"""
    print("\n=== VERIFIERING AV RESULTAT ===")

    with sqlite3.connect("../goldenstat.db") as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Visa alla Micke Lundberg spelare nu
        cursor.execute("SELECT id, name FROM players WHERE name LIKE 'Micke Lundberg%' ORDER BY id")
        players = cursor.fetchall()

        total_matches = 0
        print("Nya Micke Lundberg spelare:")
        for player in players:
            # Räkna matcher för varje spelare
            cursor.execute("""
                SELECT COUNT(*) as match_count
                FROM sub_match_participants smp
                WHERE smp.player_id = ?
            """, (player['id'],))

            match_count = cursor.fetchone()['match_count']
            total_matches += match_count

            # Räkna unika klubbar
            cursor.execute("""
                SELECT DISTINCT
                    CASE WHEN smp.team_number = 1 THEN t1.name ELSE t2.name END as club_name
                FROM sub_match_participants smp
                JOIN sub_matches sm ON smp.sub_match_id = sm.id
                JOIN matches m ON sm.match_id = m.id
                JOIN teams t1 ON m.team1_id = t1.id
                JOIN teams t2 ON m.team2_id = t2.id
                WHERE smp.player_id = ?
            """, (player['id'],))

            clubs = [row['club_name'] for row in cursor.fetchall()]

            print(f"  ID {player['id']}: {player['name']}")
            print(f"    {match_count} matcher")
            print(f"    Klubbar: {', '.join(clubs)}")

        print(f"\nTotalt antal matcher: {total_matches} (förväntat: 19)")

def main():
    print("=== MICKE LUNDBERG SPLITTING SCRIPT ===")

    # Steg 1: Analysera nuvarande situation
    current_players = analyze_current_situation()

    if not current_players:
        print("ERROR: Inga Micke Lundberg spelare hittades!")
        return

    # Bekräfta att vi har rätt spelare
    if current_players[0]['id'] != 1235:
        print(f"ERROR: Förväntade ID 1235, men fick {current_players[0]['id']}")
        return

    # Steg 2: Skapa ny spelare för Dartanjang
    dartanjang_id = create_new_players()

    # Steg 3: Uppdatera tilldelningar
    update_player_assignments(dartanjang_id)

    # Steg 4: Verifiera resultat
    verify_results()

    print("\n=== MICKE LUNDBERG SPLITTING SLUTFÖRD ===")
    print("Resultat:")
    print("  - Micke Lundberg (Spikkastarna): 16 matcher (SpikKastarna + Spikkastarna)")
    print("  - Micke Lundberg (Dartanjang): 3 matcher (Dartanjang 2A)")

if __name__ == "__main__":
    main()