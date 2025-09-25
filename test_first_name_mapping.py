#!/usr/bin/env python3
"""
Testa first name mapping funktionalitet
"""
from smart_import_handler import SmartPlayerMatcher

def test_first_name_mappings():
    """Testa first name mappings för Johan-exempel"""
    print("=== TEST AV FIRST NAME MAPPINGS ===")

    matcher = SmartPlayerMatcher("goldenstat.db")

    # Test cases från user's specification
    test_cases = [
        # Johan-exempel från Rockhangers kontext
        ("Johan", "Rockhangers SL1"),
        ("Johan", "Rockhangers (SL1)"),

        # Andra möjliga förnamn som kan ha etablerade mappningar
        ("Johan", "TYO DC"),
        ("Johan", "SpikKastarna"),

        # Testa även andra förnamn som kan ha mappningar
        ("Anders", "Dartanjang"),
        ("Mats", "Dartanjang"),
        ("Mikael", "AIK Dart"),
    ]

    print("Testar förnamn-mappningar:")

    for player_name, team_name in test_cases:
        result = matcher.find_player_match(player_name, team_name)

        print(f"\n'{player_name}' från '{team_name}':")
        print(f"  Action: {result['action']}")
        print(f"  Target: {result['player_name']}")
        print(f"  Player ID: {result.get('player_id', 'None')}")
        print(f"  Confidence: {result['confidence']}%")
        print(f"  Notes: {result['notes']}")

        # Extra info för first name mappings
        if result['action'] == 'first_name_mapping_found':
            print(f"  Original name: {result.get('original_name', 'N/A')}")
            print(f"  Mapping type: {result.get('mapping_type', 'N/A')}")

        # Visa om det är en bra kandidat för automatisk import
        if result['confidence'] >= 90:
            print(f"  [AUTO IMPORT] Hög confidence - kan användas automatiskt")
        elif result['confidence'] >= 75:
            print(f"  [REVIEW] Medium confidence - kan kräva granskning")
        else:
            print(f"  [MANUAL] Låg confidence - kräver manuell hantering")

    # Test specific known examples if they exist
    print(f"\n=== KONTROLL AV KÄNDA ETABLERADE MAPPNINGAR ===")

    # Kolla om det finns Johan-mappningar i databasen
    import sqlite3
    with sqlite3.connect("goldenstat.db") as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Sök efter Johan-mappningar
        cursor.execute("""
            SELECT DISTINCT p1.name as original_name, smpm.correct_player_name,
                   COUNT(*) as mapping_count
            FROM sub_match_player_mappings smpm
            JOIN players p1 ON smpm.original_player_id = p1.id
            WHERE p1.name LIKE 'Johan%' OR p1.name = 'Johan'
            GROUP BY p1.name, smpm.correct_player_name
            ORDER BY mapping_count DESC
        """)

        johan_mappings = cursor.fetchall()

        if johan_mappings:
            print(f"Hittade {len(johan_mappings)} Johan-relaterade mappningar:")
            for mapping in johan_mappings:
                print(f"  {mapping['original_name']} -> {mapping['correct_player_name']} ({mapping['mapping_count']} gånger)")
        else:
            print("Inga Johan-relaterade mappningar hittades i databasen")

        # Kontrollera om Johan finns som spelare
        cursor.execute("""
            SELECT id, name FROM players WHERE name = 'Johan'
        """)

        johan_players = cursor.fetchall()
        if johan_players:
            print(f"\nJohan finns som spelare:")
            for player in johan_players:
                print(f"  ID {player['id']}: {player['name']}")
        else:
            print(f"\nJohan finns INTE som spelare i databasen")

if __name__ == "__main__":
    test_first_name_mappings()