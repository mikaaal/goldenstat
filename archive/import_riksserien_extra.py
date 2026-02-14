#!/usr/bin/env python3
"""
Tilläggsimport av Riksserien - divisioner som saknades i första körningen.

Inkluderar:
- 2024-25: Elit Slutspel, Div 3A, Div 3B, Div 3C
- 2023-24: Elit, Superettan, Superettan Dam

Usage: python import_riksserien_extra.py
"""
import os
import sys
import datetime
import json
import traceback
from pathlib import Path

from generate_match_urls import MatchUrlGenerator
from smart_season_importer import SmartSeasonImporter

DB_PATH = "riksserien.db"
URL_DIR = Path("riksserien_match_urls_2024_25")

DIVISIONS = [
    # 2024-25 divisioner som saknades
    {"tdid": "t_lhOq_9663", "code": "RS3A",      "name": "Div 3A",         "season": "2024/2025"},
    {"tdid": "t_QKZr_0725", "code": "RS3B",      "name": "Div 3B",         "season": "2024/2025"},
    {"tdid": "t_IQTc_8681", "code": "RS3C",      "name": "Div 3C",         "season": "2024/2025"},
    # 2023-24 säsongen
    {"tdid": "t_JBEb_8253", "code": "RSElit",    "name": "Elit",            "season": "2023/2024"},
    {"tdid": "t_6tXn_3079", "code": "RSSup",     "name": "Superettan",      "season": "2023/2024"},
    {"tdid": "t_72J8_8179", "code": "RSSupDam",  "name": "Superettan Dam",  "season": "2023/2024"},
]


def main():
    print("=" * 60)
    print("RIKSSERIEN TILLÄGGSIMPORT")
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
            print(f"  [GEN] {div['name']} {div['season']} ({div['tdid']})...")
            success = generator.save_urls_to_file(div["tdid"], str(url_file))
            if not success:
                print(f"  [WARN] Kunde inte generera URLs för {div['name']}")

    # Steg 2: Importera varje division
    print(f"\n[STEG 2] Importerar matcher till {DB_PATH}...")

    total_matches = 0
    total_players = 0
    results = []

    for i, div in enumerate(DIVISIONS, 1):
        url_file = URL_DIR / f"{div['tdid']}_match_urls{div['code']}.txt"

        if not url_file.exists():
            print(f"\n[{i}/{len(DIVISIONS)}] [SKIP] Ingen URL-fil för {div['name']}")
            results.append({"division": div["name"], "season": div["season"], "status": "skipped", "matches": 0})
            continue

        print(f"\n[{i}/{len(DIVISIONS)}] Importerar {div['name']} {div['season']} ({div['tdid']})...")

        try:
            importer = SmartSeasonImporter(DB_PATH)
            result = importer.import_from_url_file_smart(
                str(url_file),
                div["tdid"],
                division_name=div["name"],
                season=div["season"],
            )

            matches = result.get("matches_imported", 0)
            players = result.get("players_processed", 0)
            total_matches += matches
            total_players += players

            print(f"  [OK] {matches} matcher, {players} spelare")
            results.append({"division": div["name"], "season": div["season"], "status": "ok", "matches": matches, "players": players})

        except Exception as e:
            print(f"  [ERROR] {e}")
            traceback.print_exc()
            results.append({"division": div["name"], "season": div["season"], "status": "error", "error": str(e)})

    # Sammanfattning
    print("\n" + "=" * 60)
    print("TILLÄGGSIMPORT SLUTFÖRD")
    print(f"  Totalt matcher: {total_matches}")
    print(f"  Totalt spelare: {total_players}")
    print()
    for r in results:
        status = r["status"].upper()
        matches = r.get("matches", "-")
        print(f"  {status:6s} | {r['season']} | {r['division']:20s} | {matches} matcher")
    print("=" * 60)

    # Spara logg
    log_dir = Path("import_logs")
    log_dir.mkdir(exist_ok=True)
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = log_dir / f"riksserien_extra_import_{timestamp}.json"

    log_data = {
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
