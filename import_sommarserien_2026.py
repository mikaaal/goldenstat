# -*- coding: utf-8 -*-
"""
Import av StDF & OBDT Sommarserie (2026)

Regenererar URL-filer och importerar matcher till sommarserien.db.

Usage:
  python import_sommarserien_2026.py            # Kör allt (URL-gen + import)
  python import_sommarserien_2026.py --urls     # Bara generera URL-filer
  python import_sommarserien_2026.py --import   # Bara importera (URL-filer måste finnas)
"""
import sys
import datetime
import json
import traceback
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

from generate_match_urls import MatchUrlGenerator

SEASON = "2026"
DB_PATH = "sommarserien.db"
URL_DIR = Path("sommarserien_match_urls")

DIVISIONS = [
    {"tdid": "t_CBfN_6991", "code": "SSPoolA", "name": "Pool A"},
    {"tdid": "t_TpvD_4319", "code": "SSPoolB", "name": "Pool B"},
    {"tdid": "t_Vpo9_7678", "code": "SSPoolC", "name": "Pool C"},
    {"tdid": "t_0AnH_0946", "code": "SSPoolD", "name": "Pool D"},
    {"tdid": "t_yC98_7425", "code": "SSPoolE", "name": "Pool E"},
    {"tdid": "t_VPtT_0954", "code": "SSPoolF", "name": "Pool F"},
]


def generate_urls():
    print("\n[STEG 1] Genererar match-URL-filer...")
    URL_DIR.mkdir(exist_ok=True)
    generator = MatchUrlGenerator()

    results = []
    for div in DIVISIONS:
        url_file = URL_DIR / f"{div['tdid']}_match_urls{div['code']}.txt"
        print(f"  [GEN] {div['name']} ({div['tdid']})...")
        success = generator.save_urls_to_file(div["tdid"], str(url_file))
        results.append({"division": div["name"], "ok": success})
        if not success:
            print(f"  [WARN] Kunde inte generera URLs för {div['name']}")

    ok = sum(1 for r in results if r["ok"])
    print(f"\n[URL-GEN] {ok}/{len(DIVISIONS)} divisioner OK")
    return results


def run_import():
    from sommarserien_importer import SommarserienImporter

    print(f"\n[STEG 2] Importerar matcher till {DB_PATH}...")
    total_matches = 0
    results = []

    for i, div in enumerate(DIVISIONS, 1):
        url_file = URL_DIR / f"{div['tdid']}_match_urls{div['code']}.txt"

        if not url_file.exists():
            print(f"\n[{i}/{len(DIVISIONS)}] [SKIP] Ingen URL-fil för {div['name']}")
            results.append({"division": div["name"], "status": "skipped", "matches": 0})
            continue

        print(f"\n[{i}/{len(DIVISIONS)}] Importerar {div['name']} ({div['tdid']})...")

        try:
            importer = SommarserienImporter(DB_PATH)
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

    print(f"\n{'='*60}")
    print(f"KLART! Totalt {total_matches} nya matcher importerade")
    print(f"{'='*60}")
    for r in results:
        status = r["status"]
        name = r["division"]
        if status == "ok":
            print(f"  {name}: {r['matches']} matcher")
        elif status == "skipped":
            print(f"  {name}: SKIPPED")
        else:
            print(f"  {name}: FEL - {r.get('error', '')[:60]}")

    log = {
        "timestamp": datetime.datetime.now().isoformat(),
        "season": SEASON,
        "total_matches": total_matches,
        "results": results
    }
    log_file = Path("import_logs") / f"sommarserien_2026_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    log_file.parent.mkdir(exist_ok=True)
    with open(log_file, "w", encoding="utf-8") as f:
        json.dump(log, f, indent=2, ensure_ascii=False)
    print(f"\n[LOG] {log_file}")


def main():
    print("=" * 60)
    print(f"SOMMARSERIE {SEASON} - IMPORT")
    print(f"Databas: {DB_PATH}")
    print(f"Divisioner: {len(DIVISIONS)}")
    print(f"Tid: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    args = set(sys.argv[1:])
    only_urls = "--urls" in args
    only_import = "--import" in args

    if only_urls:
        generate_urls()
    elif only_import:
        run_import()
    else:
        generate_urls()
        run_import()


if __name__ == "__main__":
    main()
