#!/usr/bin/env python3
"""
Nightly cup import script.

Fetches tournament lists from configured leagues and title searches via
the n01 API, finds tournaments not yet in cups.db, and imports them.

A normal run only searches the last RECENT_DAYS. --backfill searches back to
SEARCH_SINCE and puts everything missing in the cup_backlog table, which later
runs then work through, IMPORT_MINUTES_PER_RUN at a time.

Usage:
    python nightly_cup_import.py              # Import new completed tournaments
    python nightly_cup_import.py --dry        # Dry run - show what would be imported
    python nightly_cup_import.py --backfill   # Also queue older tournaments from the searches
"""
import os
import re
import sys
import time
import sqlite3
import json
from datetime import datetime, timedelta
import requests
from import_cup import CupImporter, tournament_date_from
from n01_api import LEAGUE_API, TOURNAMENT_API


# Leagues to monitor for new tournaments
LEAGUES = [
    {"lgid": "lg_zAAr_1368", "name": "East Cup"},
    {"lgid": "lg_qaVN_1417", "name": "SoFo House Poängsamlarcup 2027"},
    {"lgid": "lg_InWB_0595", "name": "Oilers Poängsamlarcup"},
    {"lgid": "lg_obTt_7229", "name": "NWD Poängsamlarcup"},
    {"lgid": "lg_wF2x_7591", "name": "StDF"},
    {"lgid": "lg_fz61_5884", "name": "StDF GPn"},
]

# Tournaments to skip (not real cups, test events, etc.)
SKIP_TDIDS = {
    "t_VA1z_4128",  # East Pub 23/12
    "t_51wh_1214",  # Styrelsepool
    "t_P92R_1685",  # Bees cup
    "t_JRXV_6101",  # Bee 240614
    "t_7RD1_6222",  # Ei saa peittää
    # Foreign online group that also calls itself TDC
    "t_zgCg_3016", "t_YyL8_4989", "t_fvjM_5360", "t_Qtkc_2890", "t_HCjx_0908",
    "t_Aarz_4178", "t_RQov_8471", "t_HXJf_9695", "t_dIfs_4431", "t_iW1Z_2926",
    "t_3kjj_4484", "t_zZgJ_7248", "t_LhHJ_6623", "t_mZth_9974",
    # Mongolian cups named CDC
    "t_6v3R_3003", "t_1VFp_8674",
}

# Series that are not in any league on n01 are found by searching titles instead.
# keyword is sent to n01's search, pattern must then match the title. Titles also
# have to look like a cup, so league matches against a club are not picked up.
SEARCH_SINCE = "2023-11-01"
RECENT_DAYS = 21
_CUP = r"(?=.*(cup|poängsaml|lottad|singel|dubbel|mästerskap|open|öppen|closed|\bkm\b|grand prix))"
_NOT = r"(?!.*(\btest|off season|friday|saturday|\bsat cup|cup night|double elimination|africa))"


def _club(org: str) -> str:
    return rf"^{_NOT}(?=.*{org}){_CUP}"


SEARCHES = [
    {"name": "Oilers", "keyword": "oilers", "pattern": _club(r"\boilers\b")},
    {"name": "NWD", "keyword": "nwd", "pattern": _club(r"\bnwd\b")},
    {"name": "East", "keyword": "east", "pattern": _club(r"\beasts?\b")},
    {"name": "MiNi's", "keyword": "mini", "pattern": _club(r"\bmini.?s\b")},
    {"name": "SoFo House", "keyword": "sofo", "pattern": _club(r"\bsofo\b")},
    {"name": "Kvarteret", "keyword": "kvarter", "pattern": _club(r"\bkvarter")},
    {"name": "Goldtown", "keyword": "goldtown", "pattern": _club(r"goldtown")},
    {"name": "Ludvika", "keyword": "ludvika", "pattern": _club(r"ludvika")},
    {"name": "Bankeryd", "keyword": "bankeryd", "pattern": _club(r"bankeryd")},
    {"name": "BDC", "keyword": "bdc", "pattern": _club(r"\bbdc\b")},
    {"name": "VDC", "keyword": "vdc", "pattern": _club(r"\bvdc\b")},
    {"name": "UDC", "keyword": "udc", "pattern": _club(r"\budc\b")},
    {"name": "CDC", "keyword": "cdc", "pattern": _club(r"\bcdc\b")},
    {"name": "TDC", "keyword": "tdc", "pattern": _club(r"\btdc\b")},
    {"name": "Faster Annas", "keyword": "faster anna", "pattern": _club(r"faster anna")},
    {"name": "Pennybridge", "keyword": "pennybridge", "pattern": _club(r"pennybridge")},
    {"name": "OBDC", "keyword": "obdc", "pattern": _club(r"\bobdc\b")},
    {"name": "Mjölner", "keyword": "mjölner", "pattern": _club(r"mjölner")},
    {"name": "Målilla", "keyword": "målilla", "pattern": _club(r"målilla")},
    {"name": "PDK", "keyword": "pdk", "pattern": _club(r"\bpdk\b")},
    {"name": "Tuna DC", "keyword": "tuna", "pattern": _club(r"\btunas?\b")},
    {"name": "NDK", "keyword": "ndk", "pattern": _club(r"\bndk\b")},
    {"name": "Slaggpilen", "keyword": "slaggpilen", "pattern": _club(r"slaggpilen")},
    {"name": "Två Feta Grisar", "keyword": "feta grisar", "pattern": _club(r"feta grisar")},
    {"name": "Glam", "keyword": "glam", "pattern": _club(r"\bglam\b")},
    {"name": "SSDC Closed", "keyword": "ssdc closed", "pattern": _club(r"^ssdc closed\b")},
]

# Importing takes about 15 ms per dart thrown (1-2 minutes for a normal cup, 5-6
# for a big open class), so a backfill of years of cups is spread over several
# runs. The rest is left for the next run once this many minutes have passed.
IMPORT_MINUTES_PER_RUN = 150

# Extra tournaments not in any league (imported by tdid directly)
EXTRA_TDIDS = [
    "t_IcSW_1256",  # MiNi Onsdagscup 220302
    "t_jYZ5_2448",
    "t_dyUx_3975",
    "t_cIP9_1442",
    "t_Dvrf_8758",
    "t_nFEt_0533",
    "t_67KK_2305",
    "t_ZOpc_1458",
    "t_8Q1a_0117",
    "t_ksuy_1511",
    "t_acs0_3384",
    "t_ZBGs_8927",
    "t_2mGb_9022",
    "t_MqsU_0131",
    "t_bvjQ_9939",
    "t_o95S_0177",
    "t_lwJI_6750",
    "t_MNjc_5673",
    "t_maHQ_3759",
    "t_LkY6_8629",
    "t_belt_8760",
    # SSDC Closed 2021 (finals) and 2022, older than SEARCH_SINCE
    "t_Yl69_1056", "t_yb2A_1969", "t_lXgJ_9459", "t_ekkC_4292", "t_aHEf_7191",
    "t_C1ny_1665", "t_h8SH_2901",
    "t_AuqM_2652", "t_d60X_0530", "t_olAQ_9271", "t_yoMA_7495", "t_s9oy_5389",
    "t_X9BJ_0657", "t_mPpX_1903", "t_zKWU_9776", "t_6vM1_8908", "t_FNIz_3968",
    "t_aBJt_1457",
]

# Smaller cups are not imported. They are noted in cup_skipped instead, and
# cups imported before the limit was introduced stay in the database.
MIN_PLAYERS = 12

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


def search_tournaments(search: dict, since: datetime) -> list:
    """Find completed tournaments by title, for series that are not in any league.

    n01 returns 20 at a time, newest first. Pages are fetched until since is
    reached, and only titles matching the search pattern are kept.
    """
    pattern = re.compile(search["pattern"], re.IGNORECASE)
    since = since.timestamp()
    found = []
    for skip in range(0, 2000, 20):
        url = f"{TOURNAMENT_API}?cmd=get_list&skip={skip}&count=20"
        response = requests.post(
            url,
            params={"keyword": search["keyword"]},
            json={"status": [40], "sort": "date"},
            timeout=30,
        )
        response.raise_for_status()
        page = response.json()
        if not isinstance(page, list):
            raise RuntimeError(f"API error: {page}")
        for t in page:
            # t_date is sometimes missing, fall back to the creation time
            t["t_date"] = t.get("t_date") or t.get("createTime") or 0
            # d = darts thrown, 0 means there is no match data to import
            if t["t_date"] >= since and t.get("d") and pattern.search(t["title"]):
                found.append(t)
        if len(page) < 20 or min(t["t_date"] for t in page) < since:
            break
        time.sleep(1)
    return found


def ensure_backlog_table(conn):
    conn.execute("""
        CREATE TABLE IF NOT EXISTS cup_backlog (
            tdid VARCHAR(50) PRIMARY KEY,
            title VARCHAR(255),
            t_date INTEGER,
            source VARCHAR(100),
            added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)


def ensure_skipped_table(conn):
    conn.execute("""
        CREATE TABLE IF NOT EXISTS cup_skipped (
            tdid VARCHAR(50) PRIMARY KEY,
            title VARCHAR(255),
            skipped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)


def save_skipped(tdid: str, title: str, db_path: str = "cups.db"):
    """Remember a tournament with too few players so it is never fetched again."""
    conn = sqlite3.connect(db_path)
    ensure_skipped_table(conn)
    conn.execute("INSERT OR IGNORE INTO cup_skipped (tdid, title) VALUES (?, ?)", (tdid, title))
    conn.commit()
    conn.close()


def save_backlog(tournaments: list, db_path: str = "cups.db"):
    """Queue tournaments found by --backfill for later runs."""
    conn = sqlite3.connect(db_path)
    ensure_backlog_table(conn)
    conn.executemany(
        "INSERT OR IGNORE INTO cup_backlog (tdid, title, t_date, source) VALUES (?, ?, ?, ?)",
        [(t["tdid"], t["title"], t["t_date"], t["league"]) for t in tournaments],
    )
    conn.commit()
    conn.close()


def load_backlog(db_path: str = "cups.db") -> list:
    """Queued tournaments that are not imported yet."""
    if not os.path.exists(db_path):
        return []
    conn = sqlite3.connect(db_path)
    ensure_backlog_table(conn)
    ensure_skipped_table(conn)
    conn.execute("DELETE FROM cup_backlog WHERE tdid IN (SELECT tdid FROM tournaments)"
                 " OR tdid IN (SELECT tdid FROM cup_skipped)")
    conn.commit()
    rows = conn.execute("SELECT tdid, title, t_date, source FROM cup_backlog").fetchall()
    conn.close()
    return [{"tdid": r[0], "title": r[1], "t_date": r[2] or 0, "league": r[3]} for r in rows]


def fill_missing_dates(db_path: str = "cups.db"):
    """Date tournaments imported before the start time fallback existed."""
    conn = sqlite3.connect(db_path)
    tdids = [r[0] for r in conn.execute(
        "SELECT tdid FROM tournaments WHERE tournament_date IS NULL")]
    importer = CupImporter(db_path)
    for tdid in tdids:
        try:
            date = tournament_date_from(importer.fetch_tournament_data(tdid))
        except Exception as e:
            print(f"Could not fetch date for {tdid}: {e}")
            continue
        if date:
            conn.execute("UPDATE tournaments SET tournament_date = ? WHERE tdid = ?",
                         (date, tdid))
        time.sleep(1)
    conn.commit()
    conn.close()


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
    """Get all tdids already imported or skipped for having too few players."""
    if not os.path.exists(db_path):
        return set()
    conn = sqlite3.connect(db_path)
    ensure_skipped_table(conn)
    cursor = conn.execute("SELECT tdid FROM tournaments UNION SELECT tdid FROM cup_skipped")
    tdids = {row[0] for row in cursor.fetchall()}
    conn.close()
    return tdids


def main():
    dry_run = "--dry" in sys.argv
    backfill = "--backfill" in sys.argv

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
                        "t_date": t.get("t_date") or 0,
                    })
        except Exception as e:
            print(f"  ERROR fetching {name}: {e}")

    queued = {t["tdid"] for t in new_tournaments}
    if backfill:
        since = datetime.fromisoformat(SEARCH_SINCE)
    else:
        since = datetime.now() - timedelta(days=RECENT_DAYS)
    found = []
    for search in SEARCHES:
        name = search["name"]
        print(f"\nSearching {name} ('{search['keyword']}')...")
        try:
            tournaments = search_tournaments(search, since)
            print(f"  Found {len(tournaments)} completed tournaments")
            for t in tournaments:
                tdid = t["tdid"]
                if tdid not in existing and tdid not in SKIP_TDIDS and tdid not in queued:
                    queued.add(tdid)
                    found.append({
                        "tdid": tdid,
                        "title": t["title"],
                        "league": name,
                        "t_date": t["t_date"],
                    })
        except Exception as e:
            print(f"  ERROR searching {name}: {e}")
        time.sleep(1)
    new_tournaments += found

    if backfill and not dry_run:
        save_backlog(found)
        print(f"\nQueued {len(found)} tournaments in cup_backlog")

    for t in load_backlog():
        if t["tdid"] not in existing and t["tdid"] not in SKIP_TDIDS and t["tdid"] not in queued:
            queued.add(t["tdid"])
            new_tournaments.append(t)

    # Add extra standalone tournaments not in any league
    for tdid in EXTRA_TDIDS:
        if tdid not in existing and tdid not in SKIP_TDIDS and tdid not in queued:
            new_tournaments.append({
                "tdid": tdid,
                "title": tdid,
                "league": "Extra",
                "t_date": 0,
            })

    if not new_tournaments:
        print("\nNo new tournaments to import.")
        return 0

    # Newest first, so this week's cups are not held up by the historical backfill
    new_tournaments.sort(key=lambda t: t["t_date"], reverse=True)

    print(f"\nNew tournaments to import: {len(new_tournaments)}")
    for t in new_tournaments:
        print(f"  [{t['league']}] {t['tdid']} - {t['title']}")

    if dry_run:
        print("\nDry run - nothing imported.")
        return 0

    # Import new tournaments
    success = 0
    skipped = 0
    failed = []
    deadline = time.monotonic() + IMPORT_MINUTES_PER_RUN * 60

    for i, t in enumerate(new_tournaments, 1):
        if time.monotonic() > deadline:
            print(f"\nTime budget of {IMPORT_MINUTES_PER_RUN} minutes used, "
                  f"{len(new_tournaments) - i + 1} tournaments left for later runs")
            break
        tdid = t["tdid"]
        title = t["title"]
        print(f"\n{'='*60}")
        print(f"[{i}/{len(new_tournaments)}] {title} ({tdid})")
        print(f"{'='*60}")

        importer = CupImporter()
        try:
            if importer.import_tournament(tdid, min_players=MIN_PLAYERS):
                success += 1
            else:
                save_skipped(tdid, title)
                skipped += 1
        except Exception as e:
            print(f"FAILED: {e}")
            failed.append((tdid, title, str(e)))

        if i < len(new_tournaments):
            time.sleep(2)

    fill_missing_dates()
    apply_date_fixes()

    print(f"\n{'='*60}")
    print(f"DONE: {success} imported, {skipped} skipped, {len(failed)} failed")
    if failed:
        print("\nFailed tournaments:")
        for tdid, title, err in failed:
            print(f"  {tdid} ({title}): {err}")

    # During a backfill one bad tournament must not fail the step, since the
    # workflow then skips the upload and every import from the run is lost
    return 0 if success or skipped else 1


if __name__ == "__main__":
    sys.exit(main())
