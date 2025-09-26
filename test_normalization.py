#!/usr/bin/env python3
"""
Testa name normalization
"""
from database import DartDatabase

def test_normalization():
    """Testa att name normalization fungerar korrekt"""
    print("=== TESTAR NAME NORMALIZATION ===")

    db = DartDatabase()

    test_cases = [
        ("mikael granath", "Mikael Granath"),
        ("LARS ROSEN", "Lars Rosen"),
        ("johan (rockhangers)", "Johan (Rockhangers)"),
        ("Petra (Sweden Capital)", "Petra (Sweden Capital)"),
        ("anna-karin", "Anna-karin"),
        ("  extra  spaces  ", "Extra Spaces"),
        ("", ""),
        (None, None)
    ]

    print("Testfall för normalisering:")
    for input_name, expected in test_cases:
        if input_name is None:
            result = db.normalize_player_name(input_name)
            print(f"  '{input_name}' -> '{result}' ({'OK' if result == expected else 'FAIL'})")
        else:
            result = db.normalize_player_name(input_name)
            print(f"  '{input_name}' -> '{result}' ({'OK' if result == expected else 'FAIL'})")

    print("\nTestar get_or_create_player med case-variationer:")

    # Test 1: Första versionen skapar spelaren
    id1 = db.get_or_create_player("mikael granath")
    print(f"get_or_create_player('mikael granath') -> ID: {id1}")

    # Test 2: Case-variation ska ge samma ID
    id2 = db.get_or_create_player("Mikael Granath")
    print(f"get_or_create_player('Mikael Granath') -> ID: {id2}")

    # Test 3: Annan case-variation ska också ge samma ID
    id3 = db.get_or_create_player("MIKAEL GRANATH")
    print(f"get_or_create_player('MIKAEL GRANATH') -> ID: {id3}")

    if id1 == id2 == id3:
        print("[OK] Alla case-variationer gav samma spelare-ID!")
    else:
        print(f"[ERROR] Case-variationer gav olika ID: {id1}, {id2}, {id3}")

    # Verifiera att rätt namn sparats i databasen
    import sqlite3
    with sqlite3.connect("goldenstat.db") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM players WHERE id = ?", (id1,))
        result = cursor.fetchone()
        actual_name = result[0] if result else None
        print(f"Namn i databas: '{actual_name}'")

        if actual_name == "Mikael Granath":
            print("[OK] Normaliserat namn sparat korrekt!")
        else:
            print(f"[ERROR] Förväntat 'Mikael Granath', fick '{actual_name}'")

if __name__ == "__main__":
    test_normalization()