#!/usr/bin/env python3
"""
Bootstrap match-URL-filer for en ny sasong.

Hamtar divisionslistan for en liga direkt fran Nakka (get_season_list) och
genererar en URL-fil per division i current_match_urls/.

Anvands nar en ny sasong laggs upp och current_match_urls ar tom - da kan
generate_all_match_urls.py inte anvandas eftersom den utgar fran befintliga
filer.

Usage:
    python generate_season_match_urls.py [lgid] [--out DIR] [--dry-run]

Default lgid ar StDF (Stockholms Dartforbund).
"""
import argparse
import os
import sys
from typing import Dict, List

import requests

from generate_match_urls import MatchUrlGenerator

# StDF - Stockholms Dartforbund
DEFAULT_LGID = 'lg_S4To_8117'

LEAGUE_API = 'https://tk2-228-23746.vs.sakura.ne.jp/n01/league/n01_league.php'

# 10=Preparing, 20=Accepting entries, 25=Making table, 30=In session, 40=Completed
ALL_STATUSES = [10, 20, 25, 30, 40]


def get_divisions(lgid: str, statuses: List[int] = None) -> List[Dict]:
    """Hamta alla divisioner (tournaments) for en liga"""
    statuses = statuses or ALL_STATUSES

    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'Content-Type': 'application/json',
    })

    response = session.post(
        f'{LEAGUE_API}?cmd=get_season_list&lgid={lgid}',
        json={
            'skip': 0,
            'count': 500,
            'keyword': '',
            'status': statuses,
            'sort': 'date',
            'sort_order': -1,
        },
        timeout=20,
    )
    response.raise_for_status()

    data = response.json()
    if not isinstance(data, list):
        raise RuntimeError(f'Ovantat svar fran get_season_list: {data}')

    return [d for d in data if d.get('tdid') and d.get('title')]


def safe_title(title: str) -> str:
    """Gor divisionstiteln saker att anvanda i ett filnamn"""
    return ''.join(c for c in title.strip() if c.isalnum())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('lgid', nargs='?', default=DEFAULT_LGID,
                        help=f'Liga-ID pa Nakka (default: {DEFAULT_LGID})')
    parser.add_argument('--out', default='current_match_urls',
                        help='Katalog att skriva URL-filer till')
    parser.add_argument('--dry-run', action='store_true',
                        help='Visa bara vad som skulle genereras')
    args = parser.parse_args()

    print(f'Hamtar divisioner for liga {args.lgid}')
    divisions = get_divisions(args.lgid)

    if not divisions:
        print('ERROR: Inga divisioner hittades')
        return 1

    divisions.sort(key=lambda d: d['title'])

    print(f'\nHittade {len(divisions)} divisioner:')
    for d in divisions:
        print(f"   {d['tdid']}  {d['title']}  (status={d['status']})")

    if args.dry_run:
        print('\n--dry-run: inga filer skrivna')
        return 0

    os.makedirs(args.out, exist_ok=True)

    generator = MatchUrlGenerator()
    failed = []

    for i, d in enumerate(divisions, 1):
        tdid = d['tdid']
        title = safe_title(d['title'])
        output_file = os.path.join(args.out, f'{tdid}_match_urls{title}.txt')

        print(f"\n{'='*60}")
        print(f"[{i}/{len(divisions)}] {d['title']} ({tdid}) -> {os.path.basename(output_file)}")
        print('='*60)

        if not generator.save_urls_to_file(tdid, output_file):
            failed.append(f"{d['title']} ({tdid})")

    print(f"\n{'='*60}")
    print(f'Klart: {len(divisions) - len(failed)}/{len(divisions)} divisioner')
    if failed:
        print('Misslyckades (troligen inget spelschema upplagt an):')
        for f in failed:
            print(f'   - {f}')
    print('='*60)

    return 0


if __name__ == '__main__':
    sys.exit(main())
