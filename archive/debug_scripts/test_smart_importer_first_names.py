#!/usr/bin/env python3
"""
Testa SmartSeasonImporter med first name mapping
"""
from smart_season_importer import SmartSeasonImporter

def test_smart_importer_with_first_names():
    """Testa SmartSeasonImporter's hantering av förnamn"""
    print("=== TEST AV SMART SEASON IMPORTER MED FÖRNAMN ===")

    importer = SmartSeasonImporter("goldenstat.db")

    # Simulera några spelarnnamn som ofta förekommer som bara förnamn
    test_players = [
        ("Johan", "Rockhangers"),
        ("Johan", "TYO DC"),
        ("Anders", "Dartanjang"),
        ("Mats", "SpikKastarna"),
        ("Mikael", "AIK Dart"),
    ]

    print("Testar get_smart_player_id för förnamn:")

    for player_name, team_name in test_players:
        print(f"\nSpelare: '{player_name}' från '{team_name}'")

        try:
            # Simulera sub_match_id (skulle normalt komma från databas)
            mock_sub_match_id = 999999

            player_id = importer.get_smart_player_id(
                raw_player_name=player_name,
                team_name=team_name,
                sub_match_id=mock_sub_match_id
            )

            print(f"  → Player ID: {player_id}")

            # Hämta spelarnamnet från databasen
            import sqlite3
            with sqlite3.connect(importer.db.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM players WHERE id = ?", (player_id,))
                result = cursor.fetchone()
                if result:
                    print(f"  → Slutligt namn: {result[0]}")

        except Exception as e:
            print(f"  ERROR: {e}")

    # Visa import-statistik
    print(f"\n=== IMPORT STATISTIK ===")
    stats = importer.get_import_statistics()
    print(f"Totalt processade spelare: {stats['statistics']['total_players_processed']}")
    print(f"Auto-matched (hög confidence): {stats['statistics']['auto_matched_high_confidence']}")
    print(f"Auto-matched (medium confidence): {stats['statistics']['auto_matched_medium_confidence']}")

    # Visa sista spelarna som hanterades
    if stats['players_handled_sample']:
        print(f"\nSista spelarbeslut ({len(stats['players_handled_sample'])}):")
        for entry in stats['players_handled_sample']:
            print(f"  {entry['action']}: {entry['raw_player_name']} -> {entry['details'].get('player_name', 'N/A')}")

if __name__ == "__main__":
    test_smart_importer_with_first_names()