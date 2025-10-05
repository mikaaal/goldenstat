#!/usr/bin/env python3
"""
Test Import with Rollback Support
Tests the smart import handler with real data and provides rollback functionality
"""
import sqlite3
import json
import shutil
from datetime import datetime
from smart_import_handler import SmartPlayerMatcher
from new_format_importer import NewFormatImporter

class TestImportManager:
    def __init__(self, db_path="goldenstat.db"):
        self.db_path = db_path
        self.backup_path = f"{db_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.import_session_id = None
        self.matcher = SmartPlayerMatcher(db_path)
        self.importer = NewFormatImporter(db_path)
        self.import_log = []

    def create_backup(self):
        """Create database backup before testing"""
        print(f"Creating backup: {self.backup_path}")
        shutil.copy2(self.db_path, self.backup_path)
        return self.backup_path

    def restore_backup(self):
        """Restore database from backup"""
        if not hasattr(self, 'backup_path'):
            print("❌ No backup found!")
            return False

        print(f"🔄 Restoring from backup: {self.backup_path}")
        shutil.copy2(self.backup_path, self.db_path)
        print("✅ Database restored")
        return True

    def start_import_session(self, description):
        """Start a new import session with logging"""
        self.import_session_id = datetime.now().strftime('%Y%m%d_%H%M%S')
        session_info = {
            'session_id': self.import_session_id,
            'description': description,
            'started_at': datetime.now().isoformat(),
            'actions': []
        }

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            # Create import_sessions table if it doesn't exist
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS import_sessions (
                    id TEXT PRIMARY KEY,
                    description TEXT,
                    started_at TEXT,
                    ended_at TEXT,
                    status TEXT,
                    log_data TEXT
                )
            """)

            cursor.execute("""
                INSERT INTO import_sessions (id, description, started_at, status, log_data)
                VALUES (?, ?, ?, 'running', ?)
            """, (self.import_session_id, description, session_info['started_at'], json.dumps(session_info)))

        print(f"🚀 Started import session: {self.import_session_id}")
        return self.import_session_id

    def log_import_action(self, action_type, details):
        """Log an import action"""
        action = {
            'timestamp': datetime.now().isoformat(),
            'type': action_type,
            'details': details
        }
        self.import_log.append(action)
        print(f"📝 {action_type}: {details}")

    def process_single_match_with_smart_handler(self, match_url):
        """Process a single match using smart import handler"""
        print(f"\n🎯 Processing: {match_url}")

        # Fetch match data
        match_data = self.importer.fetch_match_data(match_url)
        if not match_data:
            self.log_import_action("FETCH_FAILED", f"Could not fetch data from {match_url}")
            return False

        # Process each player in the match using smart handler
        players_processed = []

        for match_info in match_data:
            if 'team1_players' in match_info and 'team2_players' in match_info:
                team1_name = match_info.get('team1_name', 'Unknown Team 1')
                team2_name = match_info.get('team2_name', 'Unknown Team 2')

                # Process team 1 players
                for player_name in match_info['team1_players']:
                    if player_name:  # Skip empty names
                        result = self.matcher.find_player_match(player_name, team1_name)
                        players_processed.append({
                            'original_name': player_name,
                            'team': team1_name,
                            'match_result': result
                        })

                        self.log_import_action("PLAYER_MATCH", {
                            'player': player_name,
                            'team': team1_name,
                            'action': result['action'],
                            'target': result['player_name'],
                            'confidence': result['confidence']
                        })

                # Process team 2 players
                for player_name in match_info['team2_players']:
                    if player_name:  # Skip empty names
                        result = self.matcher.find_player_match(player_name, team2_name)
                        players_processed.append({
                            'original_name': player_name,
                            'team': team2_name,
                            'match_result': result
                        })

                        self.log_import_action("PLAYER_MATCH", {
                            'player': player_name,
                            'team': team2_name,
                            'action': result['action'],
                            'target': result['player_name'],
                            'confidence': result['confidence']
                        })

        return players_processed

    def end_import_session(self, status='completed'):
        """End import session and save log"""
        if not self.import_session_id:
            return

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE import_sessions
                SET ended_at = ?, status = ?, log_data = ?
                WHERE id = ?
            """, (
                datetime.now().isoformat(),
                status,
                json.dumps(self.import_log),
                self.import_session_id
            ))

        print(f"🏁 Ended import session: {self.import_session_id} ({status})")

    def test_smart_import_sample(self, url_file, sample_size=5):
        """Test smart import with a sample of matches"""
        # Create backup
        backup_file = self.create_backup()

        # Start import session
        session_id = self.start_import_session(f"Smart import test for {url_file} (sample: {sample_size})")

        try:
            # Read match URLs
            with open(url_file, 'r') as f:
                urls = [line.strip() for line in f if line.strip() and not line.startswith('#')]

            print(f"📋 Found {len(urls)} URLs in {url_file}")
            print(f"🎲 Testing with sample of {sample_size} matches")

            # Take sample
            sample_urls = urls[:sample_size]

            all_results = []
            for i, url in enumerate(sample_urls, 1):
                print(f"\n--- Processing match {i}/{sample_size} ---")
                result = self.process_single_match_with_smart_handler(url)
                if result:
                    all_results.extend(result)

            # Summary
            print(f"\n=== SMART IMPORT TEST SUMMARY ===")
            print(f"Processed {len(sample_urls)} matches")
            print(f"Found {len(all_results)} player instances")

            # Group by action type
            action_counts = {}
            for result in all_results:
                action = result['match_result']['action']
                action_counts[action] = action_counts.get(action, 0) + 1

            print(f"\nAction distribution:")
            for action, count in sorted(action_counts.items()):
                print(f"  {action}: {count}")

            # Show examples of each action type
            print(f"\nExamples by action type:")
            for action_type in action_counts:
                examples = [r for r in all_results if r['match_result']['action'] == action_type]
                print(f"\n{action_type} ({action_counts[action_type]} total):")
                for example in examples[:3]:  # Show first 3
                    result = example['match_result']
                    print(f"  • '{example['original_name']}' + '{example['team']}' → '{result['player_name']}' ({result['confidence']}%)")

            self.end_import_session('completed')

        except Exception as e:
            print(f"❌ Import test failed: {e}")
            self.end_import_session('failed')
            raise

        return all_results

def main():
    """Main test function"""
    print("=== SMART IMPORT HANDLER TEST ===")

    manager = TestImportManager()

    # Test with t_jM8s_0341 (5 matches)
    url_file = "t_jM8s_0341_match_urls.txt"

    try:
        results = manager.test_smart_import_sample(url_file, sample_size=5)

        print(f"\n✅ Test completed successfully!")
        print(f"📊 Processed {len(results)} player instances")

        # Offer rollback option
        choice = input("\nDo you want to restore the database backup? (y/N): ").lower()
        if choice == 'y':
            manager.restore_backup()
        else:
            print(f"💾 Backup preserved at: {manager.backup_path}")

    except Exception as e:
        print(f"\n💥 Test failed: {e}")
        print("🔄 Automatically restoring backup...")
        manager.restore_backup()

if __name__ == "__main__":
    main()