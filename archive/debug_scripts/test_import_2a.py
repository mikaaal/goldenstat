#!/usr/bin/env python3
"""
Test import för 2A divisionen
"""
import sys
from pathlib import Path
from smart_season_importer import SmartSeasonImporter

def test_2a_import():
    """Testa import av 2A divisionen"""
    print("TESTAR IMPORT AV 2A DIVISIONEN")
    print("=" * 50)

    # Hitta 2A filen
    url_file = Path("2025-2026/t_jM8s_0341_match_urls2A.txt")

    if not url_file.exists():
        print(f"Kunde inte hitta: {url_file}")
        return

    print(f"Testar: {url_file}")

    # Skapa smart importer
    importer = SmartSeasonImporter("goldenstat.db")

    try:
        # Kör importen
        result = importer.import_from_url_file_smart(str(url_file), "t_jM8s_0341")

        # Visa resultat
        print("\nIMPORT SLUTFORD")
        print(f"Matcher importerade: {result['matches_imported']}")
        print(f"Spelare processade: {result['players_processed']}")

        # Detaljerad statistik
        stats = result['player_statistics']
        print(f"\nDETALJERAD SPELARSSTATISTIK:")
        print(f"  Auto-matched (hog conf): {stats['auto_matched_high_confidence']}")
        print(f"  Auto-matched (medel conf): {stats['auto_matched_medium_confidence']}")
        print(f"  Med klubb-kontext: {stats['auto_created_with_context']}")
        print(f"  Helt nya spelare: {stats['auto_created_new']}")

        # Varningar
        if result['warnings']:
            print(f"\nVARNINGAR ({len(result['warnings'])}):")
            for warning in result['warnings'][:5]:  # Visa första 5
                print(f"  - {warning}")

        # Fel
        if result['errors']:
            print(f"\nFEL ({len(result['errors'])}):")
            for error in result['errors'][:3]:  # Visa första 3
                print(f"  - {error}")

        # Visa några exempel på spelarbeslut
        import_log = importer.get_import_statistics()
        players_handled = import_log.get('players_handled_sample', [])

        if players_handled:
            print(f"\nEXEMPEL PA SPELARBESLUT ({len(players_handled)} senaste):")
            for player in players_handled[-10:]:  # Visa senaste 10
                action = player['action']
                name = player['raw_player_name']
                details = player['details']

                if action == "AUTO_ACCEPT_HIGH_CONFIDENCE":
                    print(f"  + {name} -> {details.get('player_name', 'N/A')}")
                elif action == "AUTO_ACCEPT_MEDIUM_CONFIDENCE":
                    print(f"  ? {name} -> {details.get('player_name', 'N/A')}")
                elif action == "AUTO_CREATE_WITH_CONTEXT":
                    print(f"  # {name} -> {details.get('created_name', 'N/A')}")
                elif action == "AUTO_CREATE_NEW":
                    print(f"  * {name} -> {details.get('created_name', 'N/A')}")

    except Exception as e:
        print(f"FEL UNDER IMPORT: {str(e)}")
        import traceback
        print(traceback.format_exc())

if __name__ == "__main__":
    test_2a_import()