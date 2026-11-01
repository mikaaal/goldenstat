#!/usr/bin/env python3
"""
Import older cups from the queue in cup_backlog, newest first.

The nightly import only takes cups played the last RECENT_DAYS. Older cups
wait in cup_backlog and are imported by this script now and then, a time
budget at a time. Run it from the Cup Backlog Import workflow.

Usage:
    python cup_backlog_import.py                 # Import for IMPORT_MINUTES_PER_RUN minutes
    python cup_backlog_import.py --minutes 300   # Import for 300 minutes
    python cup_backlog_import.py --search        # First search back to SEARCH_SINCE and queue what is missing
    python cup_backlog_import.py --dry           # Show the queue, import nothing
"""
import argparse
import sys
from datetime import datetime

import nightly_cup_import as nci


def describe(backlog: list):
    """Print how big the queue is and which dates it spans."""
    dates = sorted(t["t_date"] for t in backlog if t["t_date"])
    print(f"\nCups in the queue: {len(backlog)}")
    if dates:
        first = datetime.fromtimestamp(dates[0]).date()
        last = datetime.fromtimestamp(dates[-1]).date()
        print(f"Played between {first} and {last}")


def main():
    parser = argparse.ArgumentParser(description="Import older cups from cup_backlog")
    parser.add_argument("--minutes", type=int, default=nci.IMPORT_MINUTES_PER_RUN,
                        help="stop starting new cups after this many minutes")
    parser.add_argument("--search", action="store_true",
                        help=f"search back to {nci.SEARCH_SINCE} and queue cups that are missing")
    parser.add_argument("--dry", action="store_true", help="show the queue, import nothing")
    args = parser.parse_args()

    existing = nci.get_existing_tdids()
    print(f"Existing tournaments in database: {len(existing)}")

    found = []
    if args.search:
        found = nci.searched_tournaments(existing, datetime.fromisoformat(nci.SEARCH_SINCE))
        if not args.dry:
            nci.save_backlog(found)
            print(f"\nQueued {len(found)} tournaments in cup_backlog")

    backlog = [t for t in nci.load_backlog() if t["tdid"] not in nci.SKIP_TDIDS]
    if args.dry:
        queued = {t["tdid"] for t in backlog}
        backlog += [t for t in found if t["tdid"] not in queued]
    describe(backlog)

    return nci.import_tournaments(backlog, minutes=args.minutes, dry_run=args.dry)


if __name__ == "__main__":
    sys.exit(main())
