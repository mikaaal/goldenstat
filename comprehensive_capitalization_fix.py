#!/usr/bin/env python3
"""
Robust script som fixar ALL kapitalisering utan att krascha på Unicode-fel
"""
import sqlite3
from database import DartDatabase

def fix_all_capitalization_robust():
    """Fixa alla spelarnamn med robust felhantering"""
    print("=== ROBUST KAPITALISERING FIX ===")

    db = DartDatabase()

    with sqlite3.connect("goldenstat.db") as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Hämta ALLA spelare
        cursor.execute("SELECT id, name FROM players ORDER BY id")
        all_players = cursor.fetchall()

        print(f"Kontrollerar {len(all_players)} spelare...")

        updates_made = 0
        errors = 0

        for i, player in enumerate(all_players):
            try:
                player_id = player['id']
                current_name = player['name']

                # Testa normalisering
                normalized_name = db.normalize_player_name(current_name)

                # Om namnet behöver ändras
                if current_name != normalized_name:
                    # Visa endast ASCII-säkra tecken för att undvika Unicode-fel
                    try:
                        print(f"ID {player_id}: Uppdaterar namn")
                    except:
                        print(f"ID {player_id}: Uppdaterar namn (Unicode-tecken)")

                    # Uppdatera player namn
                    cursor.execute("UPDATE players SET name = ? WHERE id = ?",
                                 (normalized_name, player_id))

                    # Uppdatera mappningar
                    cursor.execute("""
                        UPDATE sub_match_player_mappings
                        SET correct_player_name = ?
                        WHERE correct_player_id = ?
                    """, (normalized_name, player_id))

                    updates_made += 1

                # Visa progress var 500:e spelare
                if (i + 1) % 500 == 0:
                    print(f"Behandlat {i + 1}/{len(all_players)} spelare...")

            except Exception as e:
                errors += 1
                print(f"Fel vid behandling av spelare ID {player['id']}: {str(e)}")
                continue

        conn.commit()

        print(f"\n[SLUTFÖRT] Uppdaterade {updates_made} spelarnamn")
        print(f"Fel: {errors}")

        # Testa några specifika fall
        print("\n=== VERIFIERING ===")
        test_cases = [
            ("Tobias sturesson", 1651),
            ("Anders johansson", 1997),
            ("janne zwierzak", 597)
        ]

        for test_name, expected_id in test_cases:
            try:
                cursor.execute("SELECT id, name FROM players WHERE id = ?", (expected_id,))
                result = cursor.fetchone()
                if result:
                    print(f"ID {expected_id}: \"{result['name']}\"")
                else:
                    print(f"ID {expected_id}: Inte hittad")
            except Exception as e:
                print(f"Fel vid verifiering av ID {expected_id}: {e}")

if __name__ == "__main__":
    fix_all_capitalization_robust()