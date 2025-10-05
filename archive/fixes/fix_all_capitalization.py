#!/usr/bin/env python3
"""
Fixa ALL felaktig kapitalisering i players-tabellen, även enstaka namn
"""
import sqlite3
from database import DartDatabase

def fix_all_capitalization():
    """Normalisera ALLA spelarnamn till korrekt kapitalisering"""
    print("=== FIXAR ALL KAPITALISERING ===")

    db = DartDatabase()

    with sqlite3.connect("goldenstat.db") as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Hämta alla spelare
        cursor.execute("SELECT id, name FROM players ORDER BY id")
        all_players = cursor.fetchall()

        updates_made = 0

        print(f"Kontrollerar {len(all_players)} spelare...")

        for player in all_players:
            player_id = player['id']
            current_name = player['name']
            normalized_name = db.normalize_player_name(current_name)

            # Om namnet behöver uppdateras
            if current_name != normalized_name:
                print(f"ID {player_id}: \"{current_name}\" -> \"{normalized_name}\"")

                # Uppdatera player namn
                cursor.execute("UPDATE players SET name = ? WHERE id = ?",
                             (normalized_name, player_id))

                # Uppdatera mappningar som refererar till detta namn
                cursor.execute("""
                    UPDATE sub_match_player_mappings
                    SET correct_player_name = ?
                    WHERE correct_player_id = ?
                """, (normalized_name, player_id))

                updates_made += 1

        conn.commit()
        print(f"\n[OK] Uppdaterade {updates_made} spelarnamn till korrekt kapitalisering")

        # Visa några exempel på resultat
        print("\n=== EXEMPEL PÅ KORRIGERADE NAMN ===")
        test_cases = [
            "janne zwierzak",
            "mikael granath",
            "lars rosen",
            "petra (sweden capital)"
        ]

        for test_name in test_cases:
            cursor.execute("SELECT id, name FROM players WHERE LOWER(name) = LOWER(?)",
                         (test_name,))
            result = cursor.fetchone()
            if result:
                print(f"  \"{test_name}\" -> \"{result['name']}\" (ID: {result['id']})")

if __name__ == "__main__":
    fix_all_capitalization()