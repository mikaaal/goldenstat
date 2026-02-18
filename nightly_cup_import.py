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
    {"lgid": "lg_qaVN_1417", "name": "SoFo House Poängsamlarcup 2027"},
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

# Extra tournaments not in any league (imported by tdid directly)
EXTRA_TDIDS = [
    "t_DO5x_0531",  # MiNi Onsdagscup 220302
    "t_gJko_5702",  # MiNi Onsdagscup 220216
    "t_Lmp5_9035",  # mini onsdagscup 220209
    "t_vFTx_2046",  # MiNi Onsdagscup 220202
    "t_OMzu_4283",  # Mini Onsdagscup 220126
    "t_kj9u_9936",  # MiNi Onsdagscup 220119
    "t_lp4p_7242",  # MiNi Onsdagscup 220112
    "t_vLmC_8818",  # MiNi Onsdagscup 220105
    "t_8t5t_4508",  # MiNi´s Fredagscup 230428
    "t_sGqy_9619",  # MiNi´s Fredagscup 230217
    "t_Syc1_1710",  # MiNi´s Fredagscup 230203
    "t_yqXb_6557",  # MiNi´s Fredagscup 230120
    "t_0fEy_8711",  # MiNi Fredagscup 220128
    "t_RwhK_4102",  # Mini Fredag Lottad seedad dubbel
    "t_dPLD_9559",  # MiNi lottad dubbelcup fredag 220211
    "t_8U51_8279",  # MiNi´s Fredagscup 220204
    "t_hQJw_9929",  # MiNi Fredagscup 220121
    "t_E2S1_4740",  # East Pub 2024 (0720)
    "t_S3m4_1478",  # East Pub 20240719
    "t_CMGI_6525",  # East Pub 20240713
    "t_eTyp_5197",  # East Pub 20240706
    "t_azqt_5597",  # East Eftercup 2024-07-13
    "t_8kSM_3963",  # East Pub 20240712
    "t_0lHE_1749",  # East Pub 20240705
    "t_JTIU_2607",  # East Pub 20240724
    "t_7o12_2258",  # East Pub 2024 (0628)
    "t_5W1x_8390",  # East Pub 20240627
    "t_7Zfy_4012",  # East sommarcup 2024-06-26
    "t_kdyu_5265",  # East Pub 20240622 MidsommardagsCup
    "t_aOMt_9094",  # East Pub Torsdag 20240620
    "t_gUEP_9922",  # East Pub 20240614 (kväll)
    "t_1si0_4651",  # East Pub 20240614
    "t_qEvk_9959",  # East Pub 20240608
    "t_3fV1_1653",  # East Pub 20240607
    "t_9NLL_0188",  # Easts Fredagscup 20240531
    "t_YWno_8559",  # East Pub 20241005
    "t_9Q1x_9783",  # East Pub 20241004
    "t_0BdF_2745",  # East Pub 20240921
    "t_S2pP_5345",  # East Pub 20240920
    "t_hdX0_1873",  # East Pub 20240914
    "t_pVd9_0229",  # East Pub 20240913
    "t_mtp9_7545",  # East Pub 20240907
    "t_DHV4_6809",  # East Pub 20240906
    "t_fWEZ_1316",  # East Pub 20240831
    "t_peXB_8017",  # East Pub 20240830
    "t_WYFC_6243",  # East Måndagscup 2408
    "t_QwQy_0333",  # East Pub 20240824
    "t_5zUZ_9362",  # East Pub 20240823
    "t_WLxb_5287",  # East Pub 20240823
    "t_AEJJ_7198",  # East Pub 20240823
    "t_Y9U2_7361",  # East Pub 20240817
    "t_V4Te_1546",  # East Pub 20240816
    "t_pAB6_2911",  # East Pub 20240809
    "t_ZW3w_5111",  # East Måndagscup 2024-08-12
    "t_rwJK_7579",  # East Pub 20240810
    "t_YF40_8420",  # East Pub 20240808
    "t_XK8w_8239",  # East Pub 20240806
    "t_TqgQ_8891",  # East Pub 20240803
    "t_RV88_8912",  # East Pub 20240802
    "t_LRmo_8224",  # East Pub 20240727 Lottad Dubbel
    "t_dUoz_5603",  # East Pub 20240727
    "t_WWbC_3601",  # East Pub 20240726
    "t_l04m_0893",  # East Final 20241214
    "t_qZ5a_5092",  # East Pub 20241213
    "t_ESdU_4072",  # East Pub 20241212
    "t_I8F4_9035",  # East Pub 20241130
    "t_h5Ig_6782",  # East Pub 20241129
    "t_3bzI_9315",  # East Pub 20241123
    "t_hqGu_6573",  # East Pub 20241116
    "t_Qehl_6205",  # East Pub 20241115
    "t_XBU4_7345",  # East Pub 20241108 Fredagscup
    "t_103s_7947",  # East Pub 20241025
    "t_Kimm_9794",  # East Torsdagscup 24-10-24
    "t_Dzu5_2680",  # East Pub 20241019
    "t_oOm8_1015",  # East Pub 20241018
    "t_tOZC_6279",  # East Pub 20241012
    "t_kMn9_5979",  # East Pub 20241011
]

# Date corrections for tournaments with wrong dates in the API
DATE_FIXES = {
    "t_ES9R_8042": "2025-08-23",  # NWD omg3 - API has 1970-01-01
    "t_sGqy_9619": "2023-02-17",  # MiNi´s Fredagscup 230217 - API has t_date=0
    "t_7o12_2258": "2024-06-28",  # East Pub 2024 - API has t_date=0
    "t_ZW3w_5111": "2024-08-12",  # East Måndagscup 2024-08-12 - API has t_date=0
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

    # Add extra standalone tournaments not in any league
    for tdid in EXTRA_TDIDS:
        if tdid not in existing and tdid not in SKIP_TDIDS:
            new_tournaments.append({
                "tdid": tdid,
                "title": tdid,
                "league": "Extra",
            })

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
