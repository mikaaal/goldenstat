#!/usr/bin/env python3
"""
Engångsimport av Riksserien 2024-25 säsongen.

Genererar URL-filer och importerar alla divisioner till riksserien.db.
Hoppar över Elit Slutspel.

Usage: python import_riksserien_2024_25.py
"""
import os
import sys
import datetime
import json
import traceback
from pathlib import Path

from generate_match_urls import MatchUrlGenerator
from smart_season_importer import SmartSeasonImporter

SEASON = "2024/2025"
DB_PATH = "riksserien.db"
URL_DIR = Path("riksserien_match_urls_2024_25")

# Divisioner att importera (exkl. Elit Slutspel t_WyWU_6618)
DIVISIONS = [
    {"tdid": "t_FpdO_3741", "code": "RSElit",    "name": "Elit"},
    {"tdid": "t_HBsZ_5502", "code": "RSElitDam", "name": "Elit Dam"},
    {"tdid": "t_FIVm_3872", "code": "RSSup",     "name": "Superettan"},
    {"tdid": "t_RBdf_5963", "code": "RSSupDam",  "name": "Superettan Dam"},
    {"tdid": "t_jIuD_8752", "code": "RS1A",      "name": "Div 1A"},
    {"tdid": "t_MYIn_6100", "code": "RS1B",      "name": "Div 1B"},
    {"tdid": "t_lmh5_5764", "code": "RS2A",      "name": "Div 2A"},
    {"tdid": "t_iqEl_8321", "code": "RS2B",      "name": "Div 2B"},
    {"tdid": "t_WTGr_6365", "code": "RS2C",      "name": "Div 2C"},
]


def main():
    print("=" * 60)
    print(f"RIKSSERIEN {SEASON} - ENGÅNGSIMPORT")
    print(f"Databas: {DB_PATH}")
    print(f"Divisioner: {len(DIVISIONS)}")
    print("=" * 60)

    URL_DIR.mkdir(exist_ok=True)

    # Steg 1: Generera URL-filer
    print("\n[STEG 1] Genererar match-URL-filer...")
    generator = MatchUrlGenerator()

    for div in DIVISIONS:
        url_file = URL_DIR / f"{div['tdid']}_match_urls{div['code']}.txt"
        if url_file.exists():
            print(f"  [SKIP] {url_file.name} finns redan")
        else:
            print(f"  [GEN] {div['name']} ({div['tdid']})...")
            success = generator.save_urls_to_file(div["tdid"], str(url_file))
            if not success:
                print(f"  [WARN] Kunde inte generera URLs för {div['name']}")

    # Steg 2: Importera varje division
    print(f"\n[STEG 2] Importerar matcher till {DB_PATH} med säsong {SEASON}...")

    total_matches = 0
    total_players = 0
    results = []

    for i, div in enumerate(DIVISIONS, 1):
        url_file = URL_DIR / f"{div['tdid']}_match_urls{div['code']}.txt"

        if not url_file.exists():
            print(f"\n[{i}/{len(DIVISIONS)}] [SKIP] Ingen URL-fil för {div['name']}")
            results.append({"division": div["name"], "status": "skipped", "matches": 0})
            continue

        print(f"\n[{i}/{len(DIVISIONS)}] Importerar {div['name']} ({div['tdid']})...")

        try:
            importer = SmartSeasonImporter(DB_PATH)
            result = importer.import_from_url_file_smart(
                str(url_file),
                div["tdid"],
                division_name=div["name"],
                season=SEASON,
            )

            matches = result.get("matches_imported", 0)
            players = result.get("players_processed", 0)
            total_matches += matches
            total_players += players

            print(f"  [OK] {matches} matcher, {players} spelare")
            results.append({"division": div["name"], "status": "ok", "matches": matches, "players": players})

        except Exception as e:
            print(f"  [ERROR] {e}")
            traceback.print_exc()
            results.append({"division": div["name"], "status": "error", "error": str(e)})

    # Sammanfattning
    print("\n" + "=" * 60)
    print(f"IMPORT SLUTFÖRD - {SEASON}")
    print(f"  Totalt matcher: {total_matches}")
    print(f"  Totalt spelare: {total_players}")
    print()
    for r in results:
        status = r["status"].upper()
        matches = r.get("matches", "-")
        print(f"  {status:6s} | {r['division']:20s} | {matches} matcher")
    print("=" * 60)

    # Spara logg
    log_dir = Path("import_logs")
    log_dir.mkdir(exist_ok=True)
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = log_dir / f"riksserien_2024_25_import_{timestamp}.json"

    log_data = {
        "season": SEASON,
        "timestamp": datetime.datetime.now().isoformat(),
        "total_matches": total_matches,
        "total_players": total_players,
        "results": results,
    }

    with open(log_file, "w", encoding="utf-8") as f:
        json.dump(log_data, f, indent=2, ensure_ascii=False)

    print(f"\nLogg sparad: {log_file}")


if __name__ == "__main__":
    main()
