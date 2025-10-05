#!/usr/bin/env python3
"""
Smart Full Import for Division Data
Integrates smart import handler with full match processing
"""
import json
import sqlite3
import shutil
import requests
from datetime import datetime
from smart_import_handler import SmartPlayerMatcher
from database import DartDatabase

class SmartFullImporter:
    def __init__(self, db_path="goldenstat.db"):
        self.db_path = db_path
        self.backup_path = f"{db_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.matcher = SmartPlayerMatcher(db_path)
        self.db = DartDatabase(db_path)
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/javascript, */*; q=0.01'
        })
        self.import_stats = {
            'matches_processed': 0,
            'matches_failed': 0,
            'players_exact': 0,
            'players_case_variation': 0,
            'players_club_specific': 0,
            'players_existing_mapping': 0,
            'players_new_created': 0,
            'players_failed': 0,
            'mappings_created': 0
        }

    def create_backup(self):
        """Create database backup"""
        print(f"Creating backup: {self.backup_path}")
        shutil.copy2(self.db_path, self.backup_path)
        return self.backup_path

    def restore_backup(self):
        """Restore from backup"""
        print(f"Restoring from backup: {self.backup_path}")
        shutil.copy2(self.backup_path, self.db_path)

    def fetch_match_data(self, url):
        """Fetch match data from URL"""
        try:
            response = self.session.get(url, timeout=15)
            if response.status_code == 200:
                return response.json()
            else:
                print(f"HTTP {response.status_code} for {url}")
                return None
        except Exception as e:
            print(f"Error fetching {url}: {e}")
            return None

    def process_player_with_smart_handler(self, player_name, team_name, sub_match_id):
        """Process a single player using smart handler"""
        if not player_name or not player_name.strip():
            return None

        player_name = player_name.strip()
        result = self.matcher.find_player_match(player_name, team_name)

        # Update statistics
        action = result['action']
        if action == 'exact_match':
            self.import_stats['players_exact'] += 1
        elif action == 'case_variation':
            self.import_stats['players_case_variation'] += 1
        elif action.startswith('club_specific'):
            self.import_stats['players_club_specific'] += 1
        elif action == 'existing_mapping':
            self.import_stats['players_existing_mapping'] += 1
        elif action == 'create_new':
            self.import_stats['players_new_created'] += 1
        else:
            self.import_stats['players_failed'] += 1

        # Handle different action types
        if result['player_id']:
            # Player exists, use it
            return result['player_id']

        elif action == 'create_new':
            # Create completely new player
            try:
                new_player_id = self.db.get_or_create_player(player_name)
                print(f"    Created new player: {player_name} (ID: {new_player_id})")
                return new_player_id
            except Exception as e:
                print(f"    ERROR creating player {player_name}: {e}")
                self.import_stats['players_failed'] += 1
                return None

        elif action == 'create_club_variant':
            # Create new club-specific variant
            try:
                new_player_id = self.db.get_or_create_player(result['player_name'])
                print(f"    Created club variant: {result['player_name']} (ID: {new_player_id})")
                return new_player_id
            except Exception as e:
                print(f"    ERROR creating club variant {result['player_name']}: {e}")
                self.import_stats['players_failed'] += 1
                return None

        else:
            print(f"    WARNING: Unhandled action {action} for {player_name}")
            self.import_stats['players_failed'] += 1
            return None

    def process_single_match(self, url, match_index, total_matches):
        """Process a single match URL"""
        print(f"\n[{match_index}/{total_matches}] Processing: {url}")

        match_data = self.fetch_match_data(url)
        if not match_data:
            self.import_stats['matches_failed'] += 1
            return False

        try:
            for match_info in match_data:
                # Extract basic match info
                title = match_info.get('title', 'Unknown Match')
                start_time = match_info.get('startTime', 0)

                print(f"  Match: {title}")

                # Extract teams and players from statsData
                if 'statsData' in match_info and len(match_info['statsData']) >= 2:
                    team1_data = match_info['statsData'][0]
                    team2_data = match_info['statsData'][1]

                    team1_name = team1_data.get('name', 'Unknown Team 1')
                    team2_name = team2_data.get('name', 'Unknown Team 2')

                    print(f"    {team1_name} vs {team2_name}")

                    # Process team 1 players
                    if 'order' in team1_data:
                        for i, player_data in enumerate(team1_data['order']):
                            player_name = player_data.get('oname', '')
                            if player_name:
                                print(f"      Team 1 Player {i+1}: {player_name}")
                                player_id = self.process_player_with_smart_handler(
                                    player_name, team1_name, None  # sub_match_id not needed for now
                                )
                                if player_id:
                                    print(f"        -> Player ID: {player_id}")

                    # Process team 2 players
                    if 'order' in team2_data:
                        for i, player_data in enumerate(team2_data['order']):
                            player_name = player_data.get('oname', '')
                            if player_name:
                                print(f"      Team 2 Player {i+1}: {player_name}")
                                player_id = self.process_player_with_smart_handler(
                                    player_name, team2_name, None  # sub_match_id not needed for now
                                )
                                if player_id:
                                    print(f"        -> Player ID: {player_id}")

            self.import_stats['matches_processed'] += 1
            return True

        except Exception as e:
            print(f"  ERROR processing match: {e}")
            self.import_stats['matches_failed'] += 1
            return False

    def run_full_import(self, url_file, max_matches=None):
        """Run full import from URL file"""
        print(f"=== SMART FULL IMPORT ===")
        print(f"URL file: {url_file}")
        print(f"Max matches: {max_matches or 'All'}")

        # Create backup
        self.create_backup()

        try:
            # Read URLs
            with open(url_file, 'r') as f:
                urls = [line.strip() for line in f if line.strip() and not line.startswith('#')]

            if max_matches:
                urls = urls[:max_matches]

            print(f"Processing {len(urls)} matches...")

            # Process each match
            for i, url in enumerate(urls, 1):
                success = self.process_single_match(url, i, len(urls))

                # Show progress every 10 matches
                if i % 10 == 0:
                    print(f"\n--- Progress: {i}/{len(urls)} matches processed ---")
                    self.show_stats()

            print(f"\n=== IMPORT COMPLETED ===")
            self.show_final_stats()

            return True

        except Exception as e:
            print(f"Import failed: {e}")
            print("Restoring backup...")
            self.restore_backup()
            return False

    def show_stats(self):
        """Show current import statistics"""
        stats = self.import_stats
        print(f"  Matches: {stats['matches_processed']} processed, {stats['matches_failed']} failed")
        print(f"  Players: {stats['players_exact']} exact, {stats['players_case_variation']} case, {stats['players_club_specific']} club, {stats['players_new_created']} new")

    def show_final_stats(self):
        """Show final import statistics"""
        stats = self.import_stats
        print(f"Matches processed: {stats['matches_processed']}")
        print(f"Matches failed: {stats['matches_failed']}")
        print(f"Players - Exact matches: {stats['players_exact']}")
        print(f"Players - Case variations: {stats['players_case_variation']}")
        print(f"Players - Club specific: {stats['players_club_specific']}")
        print(f"Players - Existing mappings: {stats['players_existing_mapping']}")
        print(f"Players - New created: {stats['players_new_created']}")
        print(f"Players - Failed: {stats['players_failed']}")

def main():
    importer = SmartFullImporter()

    try:
        # Start with a small batch first
        print("Starting with first 20 matches as test run...")
        success = importer.run_full_import("t_jM8s_0341_match_urls.txt", max_matches=20)

        if success:
            choice = input(f"\nTest run successful! Continue with all matches? (y/N): ").lower()
            if choice == 'y':
                # Run full import
                importer.run_full_import("t_jM8s_0341_match_urls.txt")
            else:
                choice = input("Restore backup from test run? (y/N): ").lower()
                if choice == 'y':
                    importer.restore_backup()
        else:
            print("Test run failed, backup already restored")

    except KeyboardInterrupt:
        print("\nImport interrupted by user")
        print("Restoring backup...")
        importer.restore_backup()

if __name__ == "__main__":
    main()