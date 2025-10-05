#!/usr/bin/env python3
"""
Import en specifik match-url fil
Usage: python single_file_import.py <filename>
Exempel: python single_file_import.py t_jM8s_0341_match_urls2A.txt
"""
import sys
import os
from pathlib import Path
from smart_season_importer import SmartSeasonImporter

def main():
    if len(sys.argv) != 2:
        print("Usage: python single_file_import.py <filename>")
        print("Exempel: python single_file_import.py t_jM8s_0341_match_urls2A.txt")
        return

    filename = sys.argv[1]

    # Hitta filen i current_match_urls mappen
    url_file = Path("current_match_urls") / filename

    if not url_file.exists():
        print(f"Fil hittades inte: {url_file}")
        print("Tillgängliga filer:")
        for file in Path("current_match_urls").glob("*_match_urls*.txt"):
            print(f"  - {file.name}")
        return

    print(f"Importerar från: {url_file}")

    # Extrahera division ID från filnamnet
    # Exempel: t_jM8s_0341_match_urls2A.txt -> division_id = t_jM8s_0341
    division_id = filename.split("_match_urls")[0]

    print(f"Division ID: {division_id}")

    # Skapa smart importer
    importer = SmartSeasonImporter("goldenstat.db")

    try:
        # Kör importen
        result = importer.import_from_url_file_smart(str(url_file), division_id)

        # Visa resultat
        print(f"\n=== IMPORT SLUTFÖRD ===")
        print(f"Matcher importerade: {result['matches_imported']}")
        print(f"Spelare processade: {result['players_processed']}")

        # Detaljerad statistik
        stats = result['player_statistics']
        print(f"\nSPELARSTATISTIK:")
        print(f"  Auto-matched (hög conf): {stats['auto_matched_high_confidence']}")
        print(f"  Auto-matched (medel conf): {stats['auto_matched_medium_confidence']}")
        print(f"  Med klubb-kontext: {stats['auto_created_with_context']}")
        print(f"  Helt nya spelare: {stats['auto_created_new']}")

        # Varningar
        if result['warnings']:
            print(f"\nVARNINGAR ({len(result['warnings'])}):")
            for warning in result['warnings'][:5]:
                print(f"  - {warning}")

        # Fel
        if result['errors']:
            print(f"\nFEL ({len(result['errors'])}):")
            for error in result['errors'][:3]:
                print(f"  - {error}")

    except Exception as e:
        print(f"FEL: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()