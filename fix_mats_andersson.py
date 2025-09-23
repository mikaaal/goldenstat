#!/usr/bin/env python3
"""
Fix Mats Andersson - Split one player into multiple based on club affiliation
"""
import sqlite3

def analyze_current_situation():
    """Analyze current Mats Andersson situation"""
    print("=== ANALYS AV NUVARANDE SITUATION ===")

    with sqlite3.connect("goldenstat.db") as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Visa nuvarande spelare
        cursor.execute("SELECT id, name FROM players WHERE LOWER(name) LIKE 'mats andersson%'")
        players = cursor.fetchall()

        print("Nuvarande Mats Andersson spelare:")
        for player in players:
            print(f"  ID {player['id']}: {player['name']}")

        return players

def create_new_players():
    """Create new player entries for the different Mats Andersson"""
    print("\n=== SKAPAR NYA SPELARE ===")

    with sqlite3.connect("goldenstat.db") as conn:
        cursor = conn.cursor()

        # Skapa 3 nya spelare (vi behåller ID 185 för SpikKastarna)
        new_players = [
            ("Mats Andersson (SSDC)", "SSDC-spelaren"),
            ("Mats Andersson (Dartanjang)", "Dartanjang-spelaren"),
            ("Mats Andersson (AIK Dart)", "AIK Dart-spelaren")
        ]

        created_ids = []
        for name, description in new_players:
            cursor.execute("INSERT INTO players (name) VALUES (?)", (name,))
            new_id = cursor.lastrowid
            created_ids.append(new_id)
            print(f"Skapade: ID {new_id} - {name} ({description})")

        conn.commit()
        return created_ids

def update_player_assignments():
    """Update sub_match_participants with correct player IDs"""
    print("\n=== UPPDATERAR SPELARE-TILLDELNINGAR ===")

    with sqlite3.connect("goldenstat.db") as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Hämta de nya spelare-IDn
        cursor.execute("SELECT id, name FROM players WHERE name LIKE 'Mats Andersson (%'")
        rows = cursor.fetchall()
        new_players = {row['name']: row['id'] for row in rows}

        # Definiera mappningar baserat på klubb
        club_mappings = {
            'SSDC': new_players.get('Mats Andersson (SSDC)'),
            'Dartanjang': new_players.get('Mats Andersson (Dartanjang)'),
            'AIK Dart': new_players.get('Mats Andersson (AIK Dart)'),
            # SpikKastarna behåller original ID 185
        }

        print("Klubb-mappningar:")
        for club, player_id in club_mappings.items():
            if player_id:
                print(f"  {club} -> Player ID {player_id}")
            else:
                print(f"  SpikKastarna -> Player ID 185 (original)")

        # Uppdatera SSDC matcher
        if club_mappings['SSDC']:
            cursor.execute("""
                UPDATE sub_match_participants
                SET player_id = ?
                WHERE player_id = 185
                AND sub_match_id IN (
                    SELECT sm.id
                    FROM sub_matches sm
                    JOIN matches m ON sm.match_id = m.id
                    JOIN teams t ON (
                        CASE WHEN sub_match_participants.team_number = 1
                        THEN m.team1_id ELSE m.team2_id END
                    ) = t.id
                    WHERE t.name LIKE 'SSDC%'
                )
            """, (club_mappings['SSDC'],))
            ssdc_updated = cursor.rowcount
            print(f"Uppdaterade {ssdc_updated} SSDC matcher")

        # Uppdatera Dartanjang matcher
        if club_mappings['Dartanjang']:
            cursor.execute("""
                UPDATE sub_match_participants
                SET player_id = ?
                WHERE player_id = 185
                AND sub_match_id IN (
                    SELECT sm.id
                    FROM sub_matches sm
                    JOIN matches m ON sm.match_id = m.id
                    JOIN teams t ON (
                        CASE WHEN sub_match_participants.team_number = 1
                        THEN m.team1_id ELSE m.team2_id END
                    ) = t.id
                    WHERE t.name LIKE 'Dartanjang%'
                )
            """, (club_mappings['Dartanjang'],))
            dartanjang_updated = cursor.rowcount
            print(f"Uppdaterade {dartanjang_updated} Dartanjang matcher")

        # Uppdatera AIK Dart matcher
        if club_mappings['AIK Dart']:
            cursor.execute("""
                UPDATE sub_match_participants
                SET player_id = ?
                WHERE player_id = 185
                AND sub_match_id IN (
                    SELECT sm.id
                    FROM sub_matches sm
                    JOIN matches m ON sm.match_id = m.id
                    JOIN teams t ON (
                        CASE WHEN sub_match_participants.team_number = 1
                        THEN m.team1_id ELSE m.team2_id END
                    ) = t.id
                    WHERE t.name LIKE 'AIK%Dart%'
                )
            """, (club_mappings['AIK Dart'],))
            aik_updated = cursor.rowcount
            print(f"Uppdaterade {aik_updated} AIK Dart matcher")

        # Hantera Mats andersson (ID 1851) - flytta till SpikKastarna (ID 185)
        cursor.execute("UPDATE sub_match_participants SET player_id = 185 WHERE player_id = 1851")
        moved_from_1851 = cursor.rowcount
        print(f"Flyttade {moved_from_1851} matcher från Mats andersson (1851) till SpikKastarna (185)")

        # Ta bort den tomma spelaren (1851)
        cursor.execute("DELETE FROM players WHERE id = 1851")
        print("Tog bort tom spelare ID 1851")

        # Uppdatera originalspelaren till SpikKastarna
        cursor.execute("UPDATE players SET name = 'Mats Andersson (SpikKastarna)' WHERE id = 185")
        print("Uppdaterade original spelare (185) till 'Mats Andersson (SpikKastarna)'")

        conn.commit()

def verify_results():
    """Verify the results of the split"""
    print("\n=== VERIFIERING AV RESULTAT ===")

    with sqlite3.connect("goldenstat.db") as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Visa alla Mats Andersson spelare nu
        cursor.execute("SELECT id, name FROM players WHERE name LIKE 'Mats Andersson%' ORDER BY id")
        players = cursor.fetchall()

        print("Nya Mats Andersson spelare:")
        for player in players:
            # Räkna matcher för varje spelare
            cursor.execute("""
                SELECT COUNT(*) as match_count,
                       COUNT(DISTINCT t.name) as team_count
                FROM sub_match_participants smp
                JOIN sub_matches sm ON smp.sub_match_id = sm.id
                JOIN matches m ON sm.match_id = m.id
                JOIN teams t ON (
                    CASE WHEN smp.team_number = 1 THEN m.team1_id ELSE m.team2_id END
                ) = t.id
                WHERE smp.player_id = ?
            """, (player['id'],))

            stats = cursor.fetchone()
            print(f"  ID {player['id']}: {player['name']}")
            print(f"    {stats['match_count']} matcher, {stats['team_count']} olika lag")

def main():
    print("=== MATS ANDERSSON SPLITTING SCRIPT ===")

    # Steg 1: Analysera nuvarande situation
    current_players = analyze_current_situation()

    # Steg 2: Skapa nya spelare
    new_ids = create_new_players()

    # Steg 3: Uppdatera tilldelningar
    update_player_assignments()

    # Steg 4: Verifiera resultat
    verify_results()

    print("\n=== MATS ANDERSSON SPLITTING SLUTFÖRD ===")

if __name__ == "__main__":
    main()