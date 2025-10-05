#!/usr/bin/env python3
"""
Mappa bindestreck/mellanslag variationer för spelare med både för- och efternamn
"""
import sqlite3

def map_hyphen_space_variations():
    """Mappa bindestreck vs mellanslag variationer"""
    print("=== MAPPA BINDESTRECK/MELLANSLAG VARIATIONER ===")

    # Definiera mappningarna (original_id, correct_id, beskrivning)
    # Vi väljer den med flest matcher som "korrekt"
    mappings = [
        # Anna-Lena Olsson (18) -> Anna Lena Olsson (3) - Behåll bindestreck
        (1504, 29, "Anna-Lena Olsson", "3 -> 18 matcher"),

        # Lars-Erik Renström - nära balanserat men behåll bindestreck (26 > 23)
        (1091, 1884, "Lars-Erik Renström", "23 -> 26 matcher"),

        # Maria-Eugenia Pinzon (27) -> Maria Eugenia Pinzon (1) - Behåll bindestreck
        (1514, 1166, "Maria-Eugenia Pinzon", "1 -> 27 matcher"),

        # Per-Erik Bredberg - välj den med flest (40 > 9)
        (1002, 1060, "Per-Erik Bredberg", "9 -> 40 matcher"),

        # Per-erik Bredberg -> Per-Erik Bredberg (case + bindestreck, båda -> den största)
        (1844, 1060, "Per-Erik Bredberg", "16 -> 40 matcher"),
    ]

    with sqlite3.connect("goldenstat.db") as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        print(f"Skapar mappningar för {len(mappings)} bindestreck/mellanslag variationer...")

        mappings_created = 0

        for original_id, correct_id, correct_name, reason in mappings:
            # Hämta spelarna för verifiering
            cursor.execute("SELECT name FROM players WHERE id = ?", (original_id,))
            original = cursor.fetchone()
            cursor.execute("SELECT name FROM players WHERE id = ?", (correct_id,))
            correct = cursor.fetchone()

            if not original or not correct:
                print(f"VARNING: Spelare ID {original_id} eller {correct_id} existerar inte!")
                continue

            print(f"\nMappar: '{original['name']}' -> '{correct['name']}'")
            print(f"Anledning: {reason}")

            # Skapa mappningar för alla sub-matcher där original spelare deltog
            cursor.execute("""
                INSERT OR IGNORE INTO sub_match_player_mappings (
                    sub_match_id,
                    original_player_id,
                    correct_player_id,
                    correct_player_name,
                    match_context,
                    confidence,
                    mapping_reason,
                    notes
                )
                SELECT DISTINCT
                    smp.sub_match_id,
                    ?,
                    ?,
                    ?,
                    'Hyphen/space variation mapping',
                    98,
                    'Bindestreck/mellanslag variation',
                    ?
                FROM sub_match_participants smp
                WHERE smp.player_id = ?
            """, (original_id, correct_id, correct_name, reason, original_id))

            added = cursor.rowcount
            mappings_created += added
            print(f"  Skapade {added} mappningar")

        conn.commit()
        print(f"\n=== SLUTFÖRT ===")
        print(f"Totalt skapade {mappings_created} mappningar för bindestreck/mellanslag variationer")

def verify_mappings():
    """Verifiera att mappningarna skapades korrekt"""
    print(f"\n=== VERIFIERING ===")

    with sqlite3.connect("goldenstat.db") as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Kontrollera våra specifika mappningar
        test_names = [
            "Anna-Lena Olsson",
            "Lars-Erik Renström",
            "Maria-Eugenia Pinzon",
            "Per-Erik Bredberg"
        ]

        for name in test_names:
            # Räkna mappningar till denna spelare
            cursor.execute("""
                SELECT COUNT(*) as count
                FROM sub_match_player_mappings
                WHERE correct_player_name = ?
            """, (name,))

            mappings = cursor.fetchone()['count']
            print(f"{name}: {mappings} mappningar")

def main():
    print("=== BINDESTRECK/MELLANSLAG MAPPNING ===")

    # Skapa mappningarna
    map_hyphen_space_variations()

    # Verifiera resultatet
    verify_mappings()

if __name__ == "__main__":
    main()