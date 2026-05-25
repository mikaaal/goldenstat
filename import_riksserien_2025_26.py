# -*- coding: utf-8 -*-
"""
Import av Riksserien 2025/2026 - omgång 3 (maj 2026)

Regenererar URL-filer och importerar nya matcher till riksserien.db.

Usage: python import_riksserien_2025_26.py
"""
import sys
import datetime
import json
import traceback
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

from generate_match_urls import MatchUrlGenerator
from smart_season_importer import SmartSeasonImporter

SEASON = "2025/2026"
DB_PATH = "riksserien.db"
URL_DIR = Path("riksserien_match_urls")

# Alla divisioner i Riksserien 2025/2026
# tdid hämtat från befintliga URL-filer i riksserien_match_urls/
DIVISIONS = [
    {"tdid": "t_MaL9_9167", "code": "RSElit",    "name": "Elit"},
    {"tdid": "t_7Wdc_7224", "code": "RSElitDam", "name": "Elit Dam"},
    {"tdid": "t_6smw_3432", "code": "RSSup",     "name": "Superettan"},
    {"tdid": "t_iBbo_6823", "code": "RS1A",      "name": "Div 1A"},
    {"tdid": "t_DlP2_4392", "code": "RS1B",      "name": "Div 1B"},
    {"tdid": "t_gQRT_6754", "code": "RS2A",      "name": "Div 2A"},
    {"tdid": "t_LE0h_2674", "code": "RS2B",      "name": "Div 2B"},
    {"tdid": "t_HvB3_4403", "code": "RS2C",      "name": "Div 2C"},
    {"tdid": "t_1rgH_4782", "code": "RS3A",      "name": "Div 3A"},
    {"tdid": "t_qV0g_7643", "code": "RS3B",      "name": "Div 3B"},
    {"tdid": "t_OKK6_8421", "code": "RS3C",      "name": "Div 3C"},
    {"tdid": "t_fmcd_9609", "code": "RS3D",      "name": "Div 3D"},
    {"tdid": "t_2FJR_8262", "code": "RS3E",      "name": "Div 3E"},
    {"tdid": "t_e1G6_0710", "code": "RS3F",      "name": "Div 3F"},
    {"tdid": "t_FVOb_1354", "code": "RS3G",      "name": "Div 3G"},
    {"tdid": "t_2FUf_5544", "code": "RS3H",      "name": "Div 3H"},
]


def main():
    print("=" * 60)
    print(f"RIKSSERIEN {SEASON} - IMPORT (OMGANG 3)")
    print(f"Databas: {DB_PATH}")
    print(f"Divisioner: {len(DIVISIONS)}")
    print(f"Tid: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    URL_DIR.mkdir(exist_ok=True)

    # Steg 1: Regenerera URL-filer (för att fånga omgång 3)
    print("\n[STEG 1] Regenererar match-URL-filer...")
    generator = MatchUrlGenerator()

    for div in DIVISIONS:
        url_file = URL_DIR / f"{div['tdid']}_match_urls{div['code']}.txt"
        print(f"  [GEN] {div['name']} ({div['tdid']})...")
        success = generator.save_urls_to_file(div["tdid"], str(url_file))
        if not success:
            print(f"  [WARN] Kunde inte generera URLs for {div['name']}")

    # Steg 2: Importera
    print(f"\n[STEG 2] Importerar matcher till {DB_PATH}...")
    total_matches = 0
    results = []

    for i, div in enumerate(DIVISIONS, 1):
        url_file = URL_DIR / f"{div['tdid']}_match_urls{div['code']}.txt"

        if not url_file.exists():
            print(f"\n[{i}/{len(DIVISIONS)}] [SKIP] Ingen URL-fil for {div['name']}")
            results.append({"division": div["name"], "status": "skipped", "matches": 0})
            continue

        print(f"\n[{i}/{len(DIVISIONS)}] Importerar {div['name']} ({div['tdid']})...")

        try:
            importer = SmartSeasonImporter(DB_PATH)
            result = importer.import_from_url_file_smart(
                str(url_file),
                div["tdid"],
                division_name=div["name"],
                season=SEASON
            )

            matches = result.get("matches_imported", 0)
            total_matches += matches
            results.append({"division": div["name"], "status": "ok", "matches": matches})
            print(f"  [OK] {matches} nya matcher importerade")

        except Exception as e:
            print(f"  [ERROR] {e}")
            traceback.print_exc()
            results.append({"division": div["name"], "status": "error", "error": str(e), "matches": 0})

    # Sammanfattning
    print(f"\n{'='*60}")
    print(f"KLART! Totalt {total_matches} nya matcher importerade")
    print(f"{'='*60}")
    for r in results:
        status = r['status']
        m = r['matches']
        name = r['division']
        if status == 'ok':
            print(f"  {name}: {m} matcher")
        elif status == 'skipped':
            print(f"  {name}: SKIPPED")
        else:
            print(f"  {name}: FEL - {r.get('error', '')[:60]}")

    # Spara logg
    log = {
        "timestamp": datetime.datetime.now().isoformat(),
        "season": SEASON,
        "total_matches": total_matches,
        "results": results
    }
    log_file = Path("import_logs") / f"riksserien_2025_26_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    log_file.parent.mkdir(exist_ok=True)
    with open(log_file, 'w', encoding='utf-8') as f:
        json.dump(log, f, indent=2, ensure_ascii=False)
    print(f"\n[LOG] {log_file}")


if __name__ == "__main__":
    main()
