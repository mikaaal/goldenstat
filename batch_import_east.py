#!/usr/bin/env python3
"""
Batch import all EAST cups from .claude/txts/east1.txt

Usage:
    python batch_import_east.py          # Import all from east1.txt
    python batch_import_east.py east2    # Import all from east2.txt
    python batch_import_east.py --dry    # Dry run - list tdids only
"""
import sys
import os
import json
import time
from import_cup import CupImporter

TXT_DIR = os.path.join(os.path.dirname(__file__) or '.', '.claude', 'txts')


def load_tdids(path):
    """Load tdids from a JSON fragment file (missing outer brackets)."""
    with open(path, 'r', encoding='utf-8') as f:
        raw = f.read().strip()
    # Wrap in array brackets if needed
    if not raw.startswith('['):
        raw = '[' + raw
    if not raw.endswith(']'):
        raw = raw.rstrip().rstrip(',') + ']'
    entries = json.loads(raw)
    return [e['tdid'] for e in entries if e.get('tdid')]


def main():
    dry_run = '--dry' in sys.argv
    args = [a for a in sys.argv[1:] if not a.startswith('--')]

    txt_name = args[0] if args else 'east1'
    txt_file = os.path.join(TXT_DIR, f'{txt_name}.txt')

    if not os.path.exists(txt_file):
        print(f"Error: {txt_file} not found")
        return 1

    tdids = load_tdids(txt_file)
    total = len(tdids)
    print(f"Found {total} tournaments in {txt_name}.txt")

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
