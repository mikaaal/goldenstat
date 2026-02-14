#!/usr/bin/env python3
"""
Batch import all MiNi cups from .claude/txts/mini2.txt

Usage:
    python batch_import_mini2.py          # Import all
    python batch_import_mini2.py --dry    # Dry run - list tdids only
"""
import sys
import os
import json
import time
from import_cup import CupImporter

TXT_FILE = os.path.join(os.path.dirname(__file__) or '.', '.claude', 'txts', 'mini2.txt')


def load_tdids(path):
    """Load tdids from a JSON fragment file (missing outer brackets)."""
    with open(path, 'r', encoding='utf-8') as f:
        raw = f.read().strip()
    if not raw.startswith('['):
        raw = '[' + raw
    if not raw.endswith(']'):
        raw = raw.rstrip().rstrip(',') + ']'
    entries = json.loads(raw)
    return [e['tdid'] for e in entries if e.get('tdid')]


def main():
    dry_run = '--dry' in sys.argv

    tdids = load_tdids(TXT_FILE)
    total = len(tdids)
    print(f"Found {total} tournaments in {os.path.basename(TXT_FILE)}")

    if dry_run:
        for i, tdid in enumerate(tdids, 1):
            print(f"  {i}. {tdid}")
        print(f"\nDry run complete. Use without --dry to import.")
        return 0

    success = 0
    failed = []
    for i, tdid in enumerate(tdids, 1):
        print(f"\n{'='*60}")
        print(f"[{i}/{total}] Importing {tdid}")
        print(f"{'='*60}")
        try:
            importer = CupImporter()
            importer.import_tournament(tdid)
            success += 1
        except Exception as e:
            print(f"FAILED: {e}")
            failed.append((tdid, str(e)))
        time.sleep(1)

    print(f"\n{'='*60}")
    print(f"BATCH COMPLETE: {success}/{total} succeeded")
    if failed:
        print(f"Failed ({len(failed)}):")
        for tdid, err in failed:
            print(f"  - {tdid}: {err}")
    return 0 if not failed else 1


if __name__ == "__main__":
    sys.exit(main())
