#!/usr/bin/env python3
"""
Cup tournament importer for n01 tournament data.

Usage:
    python import_cup.py <tdid>
    python import_cup.py t_ALIS_0219
    python import_cup.py t_7zbm_0674
"""
import sys
import os
import json
import time
import requests
from datetime import datetime
from cup_database import CupDatabase

BASE_URL = "https://tk2-228-23746.vs.sakura.ne.jp/n01/tournament"


class CupImporter:
    def __init__(self, db_path: str = "cups.db"):
        self.db = CupDatabase(db_path)
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
        })
        self.stats = {
            'tournament': None,
            'participants': 0,
            'players': 0,
            'matches': 0,
            'matches_with_detail': 0,
            'legs': 0,
            'throws': 0,
            'errors': [],
        }

    def fetch_tournament_data(self, tdid: str) -> dict:
        """Fetch full tournament data from the n01 API."""
        url = f"{BASE_URL}/n01_tournament.php?cmd=get_data&tdid={tdid}"
        print(f"Fetching tournament data for {tdid}...")
        response = self.session.get(url, timeout=30)
        response.raise_for_status()
        return response.json()

    def fetch_set_data(self, tmid: str) -> list:
        """Fetch detailed match/leg data for a specific tmid."""
        url = f"{BASE_URL}/n01_online_t.php?cmd=get_setdata&tmid={tmid}"
        response = self.session.get(url, timeout=15)
        response.raise_for_status()
        return response.json()

    def import_tournament(self, tdid: str):
        """Main import flow for a tournament."""
        # Step 1: Fetch tournament overview
        data = self.fetch_tournament_data(tdid)

        # Determine start score from rr_setting (primary phase)
        start_score = 501
        rr_setting = data.get('rr_setting', {})
        if rr_setting.get('startScore'):
            start_score = rr_setting['startScore']

        tournament_date = None
        t_date = data.get('t_date')
        if t_date:
            tournament_date = datetime.fromtimestamp(t_date).isoformat()

        tournament_id = self.db.get_or_create_tournament({
            'tdid': tdid,
            'title': data.get('title', ''),
            'tournament_date': tournament_date,
            'status': data.get('status'),
            'team_games': data.get('team_games', 0),
            'lgid': data.get('lgid'),
            'start_score': start_score,
        })
        self.stats['tournament'] = tdid
        print(f"Tournament: {data.get('title', tdid)} (id={tournament_id})")

        team_games = data.get('team_games', 0)

        # Step 2: Process entry_list
        entry_list = data.get('entry_list', [])
        participant_map = {}  # tpid -> participant_id
        for entry in entry_list:
            tpid = entry['tpid']
            name = entry['name']
            entry_start_score = entry.get('startScore')

            participant_id = self.db.get_or_create_participant(
                tournament_id, tpid, name, entry_start_score
            )
            participant_map[tpid] = participant_id
            self.stats['participants'] += 1

            # Parse player names and link
            if team_games == 1 or ' & ' in name:
                # Doubles: split on " & "
                player_names = [n.strip() for n in name.split(' & ')]
            else:
                player_names = [name]

            for player_name in player_names:
                player_id = self.db.get_or_create_player(player_name)
                self.db.link_participant_player(participant_id, player_id)
                self.stats['players'] += 1

        print(f"Imported {len(entry_list)} participants")

        # Step 3: Process results from all phases
        # Round-robin
        rr_table = data.get('rr_table', [])
        rr_result = data.get('rr_result', [])
        rr_matches = self._process_round_robin(
            tdid, tournament_id, rr_table, rr_result, participant_map
        )
        print(f"Round-robin: {rr_matches} matches")

        # Knockout (t)
        t_table = data.get('t_table', [])
        t_result = data.get('t_result', [])
        t_matches = self._process_knockout(
            tdid, tournament_id, 't', t_table, t_result, participant_map
        )
        print(f"Knockout: {t_matches} matches")

        # B-knockout (s2)
        s2_table = data.get('s2_table', [])
        s2_result = data.get('s2_result', [])
        s2_matches = self._process_knockout(
            tdid, tournament_id, 's2', s2_table, s2_result, participant_map
        )
        print(f"B-knockout: {s2_matches} matches")

        # Step 4: Fetch detailed match data
        self._fetch_all_details(tournament_id, tdid)

        # Step 5: Log results
        self._write_log(tdid)
        self._print_summary()

    def _process_round_robin(self, tdid, tournament_id, rr_table, rr_result, participant_map):
        """Process round-robin phase results."""
        match_count = 0
        for group_index, group in enumerate(rr_table):
            if group_index >= len(rr_result):
                continue
            group_results = rr_result[group_index]

            # Each participant plays every other participant (directional)
            for tpid1 in group:
                if tpid1 not in group_results:
                    continue
                p1_results = group_results[tpid1]
                for tpid2, result in p1_results.items():
                    if tpid2 == tpid1:
                        continue

                    p1_id = participant_map.get(tpid1)
                    p2_id = participant_map.get(tpid2)
                    if not p1_id or not p2_id:
                        continue

                    tmid = f"{tdid}_rr_{group_index}_{tpid1}_{tpid2}"

                    # result['r'] = legs won by tpid1, result['a'] = average
                    # We need to find tpid2's result against tpid1 for their legs
                    p2_result = group_results.get(tpid2, {}).get(tpid1, {})

                    self.db.insert_cup_match({
                        'tournament_id': tournament_id,
                        'phase': 'rr',
                        'phase_detail': str(group_index),
                        'participant1_id': p1_id,
                        'participant2_id': p2_id,
                        'p1_legs_won': result.get('r', 0),
                        'p2_legs_won': p2_result.get('r', 0),
                        'p1_average': result.get('a'),
                        'p2_average': p2_result.get('a'),
                        'tmid': tmid,
                        'has_detail': 0,
                    })
                    match_count += 1
                    self.stats['matches'] += 1

        return match_count

    def _process_knockout(self, tdid, tournament_id, phase, table, results, participant_map):
        """Process knockout phase (t or s2) results."""
        match_count = 0
        for round_index, round_entries in enumerate(table):
            if round_index >= len(results):
                continue
            round_results = results[round_index]

            # Pair consecutive entries, skip byes (empty strings)
            i = 0
            while i < len(round_entries) - 1:
                tpid1 = round_entries[i]
                tpid2 = round_entries[i + 1]
                i += 2

                # Skip if either is a bye
                if not tpid1 or not tpid2:
                    continue

                p1_id = participant_map.get(tpid1)
                p2_id = participant_map.get(tpid2)
                if not p1_id or not p2_id:
                    continue

                # Get results for this pair
                p1_result = round_results.get(tpid1, {}).get(tpid2, {})
                p2_result = round_results.get(tpid2, {}).get(tpid1, {})

                if not p1_result and not p2_result:
                    continue

                tmid = f"{tdid}_{phase}_{round_index}_{tpid1}_{tpid2}"

                self.db.insert_cup_match({
                    'tournament_id': tournament_id,
                    'phase': phase,
                    'phase_detail': str(round_index),
                    'participant1_id': p1_id,
                    'participant2_id': p2_id,
                    'p1_legs_won': p1_result.get('r', 0),
                    'p2_legs_won': p2_result.get('r', 0),
                    'p1_average': p1_result.get('a'),
                    'p2_average': p2_result.get('a'),
                    'tmid': tmid,
                    'has_detail': 0,
                })
                match_count += 1
                self.stats['matches'] += 1

        return match_count

    def _fetch_all_details(self, tournament_id, tdid):
        """Fetch detailed leg/throw data for all matches without details."""
        matches = self.db.get_matches_without_detail(tournament_id)
        total = len(matches)
        print(f"\nFetching detail data for {total} matches...")

        for i, match in enumerate(matches, 1):
            tmid = match['tmid']
            match_id = match['id']
            p1_tpid = match['p1_tpid']
            p2_tpid = match['p2_tpid']

            print(f"  [{i}/{total}] {match['phase']}:{match['phase_detail']} {p1_tpid} vs {p2_tpid}", end="")

            try:
                set_data = self.fetch_set_data(tmid)

                # If empty, try reversed tpid order
                if not set_data or set_data == []:
                    alt_parts = tmid.rsplit('_', 2)
                    if len(alt_parts) == 3:
                        alt_tmid = f"{alt_parts[0]}_{alt_parts[2]}_{alt_parts[1]}"
                        set_data = self.fetch_set_data(alt_tmid)

                if set_data and set_data != []:
                    self._import_set_data(match_id, set_data)
                    self.db.mark_match_has_detail(match_id)
                    self.stats['matches_with_detail'] += 1
                    print(" OK")
                else:
                    print(" (no data)")

            except Exception as e:
                error_msg = f"Error fetching detail for {tmid}: {e}"
                print(f" ERROR: {e}")
                self.stats['errors'].append(error_msg)

            time.sleep(0.5)

    def _import_set_data(self, cup_match_id: int, set_data: list):
        """Import leg and throw data from set_data API response."""
        # set_data is a list of sub-matches; for cups typically just one
        for submatch in set_data:
            leg_data_list = submatch.get('legData', [])
            for leg_index, leg_data in enumerate(leg_data_list, 1):
                self._import_leg(cup_match_id, leg_index, leg_data)

    def _import_leg(self, cup_match_id: int, leg_number: int, leg_data: dict):
        """Import a single leg with its throws. Same logic as new_season_importer.py."""
        try:
            winner_side = leg_data.get('winner', 0) + 1  # 0/1 -> 1/2
            first_side = leg_data.get('first', 0) + 1
            total_rounds = leg_data.get('currentRound', 0)

            leg_id = self.db.insert_leg({
                'cup_match_id': cup_match_id,
                'leg_number': leg_number,
                'winner_side': winner_side,
                'first_side': first_side,
                'total_rounds': total_rounds,
            })
            self.stats['legs'] += 1

            # Process throws for both sides
            player_data = leg_data.get('playerData', [])
            for side_index, side_throws in enumerate(player_data):
                side_number = side_index + 1

                for round_index, throw_data in enumerate(side_throws):
                    score = throw_data.get('score', 0)
                    remaining = throw_data.get('left', 501)

                    # First row (score=0) is starting position, skip
                    if round_index == 0 and score == 0:
                        continue

                    round_number = round_index  # 1-based after skipping index 0

                    # Negative score = checkout: abs(score) = darts used
                    darts_used = 3
                    if score < 0:
                        darts_used = abs(score)
                        score = remaining + abs(score)

                    self.db.insert_throw({
                        'leg_id': leg_id,
                        'side_number': side_number,
                        'round_number': round_number,
                        'score': score,
                        'remaining_score': remaining,
                        'darts_used': darts_used,
                    })
                    self.stats['throws'] += 1

        except Exception as e:
            self.stats['errors'].append(f"Error importing leg {leg_number} for match {cup_match_id}: {e}")

    def _write_log(self, tdid: str):
        """Write import log to import_logs directory."""
        log_dir = os.path.join(os.path.dirname(__file__) or '.', 'import_logs')
        os.makedirs(log_dir, exist_ok=True)

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        log_path = os.path.join(log_dir, f"cup_{tdid}_{timestamp}.json")

        with open(log_path, 'w', encoding='utf-8') as f:
            json.dump(self.stats, f, indent=2, ensure_ascii=False, default=str)

        print(f"Log written to {log_path}")

    def _print_summary(self):
        """Print import summary."""
        print(f"\n--- Import Summary ---")
        print(f"Tournament:    {self.stats['tournament']}")
        print(f"Participants:  {self.stats['participants']}")
        print(f"Players:       {self.stats['players']}")
        print(f"Matches:       {self.stats['matches']}")
        print(f"With detail:   {self.stats['matches_with_detail']}")
        print(f"Legs:          {self.stats['legs']}")
        print(f"Throws:        {self.stats['throws']}")
        if self.stats['errors']:
            print(f"Errors:        {len(self.stats['errors'])}")
            for err in self.stats['errors']:
                print(f"  - {err}")


def main():
    if len(sys.argv) < 2:
        print("Usage: python import_cup.py <tdid>")
        print("Example: python import_cup.py t_ALIS_0219")
        print("Example: python import_cup.py t_7zbm_0674")
        return 1

    tdid = sys.argv[1]
    importer = CupImporter()
    try:
        importer.import_tournament(tdid)
    except Exception as e:
        print(f"Fatal error: {e}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
