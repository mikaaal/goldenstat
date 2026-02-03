#!/usr/bin/env python3
"""
Nightly cup import script.

Fetches tournament lists from configured leagues via the n01 API,
finds tournaments not yet in cups.db, and imports them.

Usage:
    python nightly_cup_import.py          # Import new completed tournaments
    python nightly_cup_import.py --dry    # Dry run - show what would be imported
"""
import os
import sys
import time
import sqlite3
import json
import requests
from import_cup import CupImporter

LEAGUE_API = "https://tk2-228-23746.vs.sakura.ne.jp/n01/league/n01_league.php"

# Leagues to monitor for new tournaments
LEAGUES = [
    {"lgid": "lg_zAAr_1368", "name": "East Cup"},
    {"lgid": "lg_w7Bw_7076", "name": "SoFo House Poängsamlarcup"},
    {"lgid": "lg_InWB_0595", "name": "Oilers Poängsamlarcup"},
    {"lgid": "lg_V27R_4845", "name": "NWD Poängsamlarcup"},
    {"lgid": "lg_wF2x_7591", "name": "StDF"},
]

# Tournaments to skip (not real cups, test events, etc.)
SKIP_TDIDS = {
    "t_VA1z_4128",  # East Pub 23/12
    "t_51wh_1214",  # Styrelsepool
    "t_P92R_1685",  # Bees cup
    "t_JRXV_6101",  # Bee 240614
    "t_7RD1_6222",  # Ei saa peittää
}

# Date corrections for tournaments with wrong dates in the API
DATE_FIXES = {
    "t_ES9R_8042": "2025-08-23",  # NWD omg3 - API has 1970-01-01
}


def fetch_league_tournaments(lgid: str) -> list:
    """Fetch all completed tournaments from a league."""
    url = f"{LEAGUE_API}?cmd=get_season_list&lgid={lgid}"
    payload = {
        "skip": 0,
        "count": 500,
        "keyword": "",
        "status": [40],  # Only completed tournaments
        "sort": "date",
        "sort_order": -1,
    }
    response = requests.post(url, json=payload, timeout=30)
    response.raise_for_status()
    data = response.json()
    if isinstance(data, dict) and data.get("result"):
        raise RuntimeError(f"API error: {data}")
    return data


def apply_date_fixes(db_path: str = "cups.db"):
    """Fix known incorrect tournament dates after import."""
    if not DATE_FIXES:
        return
    conn = sqlite3.connect(db_path)
    for tdid, correct_date in DATE_FIXES.items():
        conn.execute(
            "UPDATE tournaments SET tournament_date = ? WHERE tdid = ?",
            (correct_date, tdid),
        )
    conn.commit()
    conn.close()


def get_existing_tdids(db_path: str = "cups.db") -> set:
    """Get all tdids already in the database."""
    if not os.path.exists(db_path):
        return set()
    conn = sqlite3.connect(db_path)
    cursor = conn.execute("SELECT tdid FROM tournaments")
    tdids = {row[0] for row in cursor.fetchall()}
    conn.close()
    return tdids


def main():
    dry_run = "--dry" in sys.argv

    existing = get_existing_tdids()
    print(f"Existing tournaments in database: {len(existing)}")

    new_tournaments = []

    for league in LEAGUES:
        lgid = league["lgid"]
        name = league["name"]
        print(f"\nFetching {name} ({lgid})...")

        try:
            tournaments = fetch_league_tournaments(lgid)
            print(f"  Found {len(tournaments)} completed tournaments")

            for t in tournaments:
                if t["tdid"] not in existing and t["tdid"] not in SKIP_TDIDS:
                    new_tournaments.append({
                        "tdid": t["tdid"],
                        "title": t["title"],
                        "league": name,
                    })
        except Exception as e:
            print(f"  ERROR fetching {name}: {e}")

    if not new_tournaments:
        print("\nNo new tournaments to import.")
        return 0

    print(f"\nNew tournaments to import: {len(new_tournaments)}")
    for t in new_tournaments:
        print(f"  [{t['league']}] {t['tdid']} - {t['title']}")

    if dry_run:
        print("\nDry run - nothing imported.")
        return 0

    # Import new tournaments
    success = 0
    failed = []

    for i, t in enumerate(new_tournaments, 1):
        tdid = t["tdid"]
        title = t["title"]
        print(f"\n{'='*60}")
        print(f"[{i}/{len(new_tournaments)}] {title} ({tdid})")
        print(f"{'='*60}")

        importer = CupImporter()
        try:
            importer.import_tournament(tdid)
            success += 1
        except Exception as e:
            print(f"FAILED: {e}")
            failed.append((tdid, title, str(e)))

        if i < len(new_tournaments):
            time.sleep(2)

    apply_date_fixes()

    print(f"\n{'='*60}")
    print(f"DONE: {success} imported, {len(failed)} failed out of {len(new_tournaments)}")
    if failed:
        print("\nFailed tournaments:")
        for tdid, title, err in failed:
            print(f"  {tdid} ({title}): {err}")

    return 0 if not failed else 1


if __name__ == "__main__":
    sys.exit(main())
