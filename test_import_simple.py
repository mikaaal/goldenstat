#!/usr/bin/env python3
"""
Simple Test Import with Smart Handler
Tests the smart import handler with real data (no emojis)
"""
import sqlite3
import json
import shutil
from datetime import datetime
from smart_import_handler import SmartPlayerMatcher
from new_format_importer import NewFormatImporter

class SimpleTestManager:
    def __init__(self, db_path="goldenstat.db"):
        self.db_path = db_path
        self.backup_path = f"{db_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.matcher = SmartPlayerMatcher(db_path)
        self.importer = NewFormatImporter(db_path)

    def create_backup(self):
        """Create database backup before testing"""
        print(f"Creating backup: {self.backup_path}")
        shutil.copy2(self.db_path, self.backup_path)
        return self.backup_path

    def restore_backup(self):
        """Restore database from backup"""
        print(f"Restoring from backup: {self.backup_path}")
        shutil.copy2(self.backup_path, self.db_path)
        print("Database restored")
        return True

    def test_single_match_url(self, match_url):
        """Test smart matching on a single match URL"""
        print(f"\nTesting match: {match_url}")

        # Fetch match data
        match_data = self.importer.fetch_match_data(match_url)
        if not match_data:
            print("  ERROR: Could not fetch match data")
            return None

        results = []

        for match_info in match_data:
            if 'team1_players' in match_info and 'team2_players' in match_info:
                team1_name = match_info.get('team1_name', 'Unknown Team 1')
                team2_name = match_info.get('team2_name', 'Unknown Team 2')

                print(f"  Match: {team1_name} vs {team2_name}")

                # Test team 1 players
                for player_name in match_info['team1_players']:
                    if player_name:
                        result = self.matcher.find_player_match(player_name, team1_name)
                        results.append({
                            'player': player_name,
                            'team': team1_name,
                            'action': result['action'],
                            'target': result['player_name'],
                            'confidence': result['confidence'],
                            'notes': result['notes']
                        })

                        print(f"    {player_name} ({team1_name})")
                        print(f"      -> {result['action']}: {result['player_name']} ({result['confidence']}%)")

                # Test team 2 players
                for player_name in match_info['team2_players']:
                    if player_name:
                        result = self.matcher.find_player_match(player_name, team2_name)
                        results.append({
                            'player': player_name,
                            'team': team2_name,
                            'action': result['action'],
                            'target': result['player_name'],
                            'confidence': result['confidence'],
                            'notes': result['notes']
                        })

                        print(f"    {player_name} ({team2_name})")
                        print(f"      -> {result['action']}: {result['player_name']} ({result['confidence']}%)")

        return results

    def test_sample_matches(self, url_file, sample_size=3):
        """Test smart import with sample matches"""

        # Create backup first
        self.create_backup()

        try:
            # Read URLs
            with open(url_file, 'r') as f:
                urls = [line.strip() for line in f if line.strip() and not line.startswith('#')]

            print(f"\nFound {len(urls)} URLs in {url_file}")
            print(f"Testing sample of {sample_size} matches")

            sample_urls = urls[:sample_size]
            all_results = []

            for i, url in enumerate(sample_urls, 1):
                print(f"\n=== MATCH {i}/{sample_size} ===")
                results = self.test_single_match_url(url)
                if results:
                    all_results.extend(results)

            # Summary
            print(f"\n=== SUMMARY ===")
            print(f"Processed {len(sample_urls)} matches")
            print(f"Found {len(all_results)} player instances")

            # Count by action type
            action_counts = {}
            for result in all_results:
                action = result['action']
                action_counts[action] = action_counts.get(action, 0) + 1

            print(f"\nAction distribution:")
            for action, count in sorted(action_counts.items()):
                print(f"  {action}: {count}")

            return all_results

        except Exception as e:
            print(f"Test failed: {e}")
            raise

def main():
    print("=== SMART IMPORT TEST ===")

    manager = SimpleTestManager()

    try:
        results = manager.test_sample_matches("t_jM8s_0341_match_urls.txt", sample_size=3)

        print(f"\nTest completed successfully!")
        print(f"Total results: {len(results)}")

        # Ask for rollback
        choice = input("\nRestore backup? (y/N): ").lower()
        if choice == 'y':
            manager.restore_backup()
        else:
            print(f"Backup saved: {manager.backup_path}")

    except Exception as e:
        print(f"Test failed: {e}")
        print("Restoring backup automatically...")
        manager.restore_backup()

if __name__ == "__main__":
    main()