#!/usr/bin/env python3
"""
Test Smart Import Handler with Real Player Data
"""
import json
import sqlite3
import shutil
from datetime import datetime
from smart_import_handler import SmartPlayerMatcher

def create_backup():
    """Create database backup"""
    backup_path = f"goldenstat.db.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    shutil.copy2("goldenstat.db", backup_path)
    print(f"Backup created: {backup_path}")
    return backup_path

def restore_backup(backup_path):
    """Restore database backup"""
    shutil.copy2(backup_path, "goldenstat.db")
    print(f"Database restored from: {backup_path}")

def test_real_players():
    """Test with real players from the API data"""

    # Test players from the match data we fetched
    test_cases = [
        ("Markus Holmqvist", "Faster Annas (2A)"),
        ("Kim Ornfjord", "Faster Annas (2A)"),  # Test without special chars
        ("Wojtek Grezsica", "AIK Dart (2A)"),
        ("Cevin Svanemar", "AIK Dart (2A)"),

        # Test some variations
        ("markus holmqvist", "Faster Annas (2A)"),  # lowercase
        ("WOJTEK GREZSICA", "AIK Dart (2A)"),      # uppercase
        ("wojtek grezsica", "AIK Dart"),            # different club format
    ]

    matcher = SmartPlayerMatcher()

    print("=== TESTING SMART IMPORT HANDLER WITH REAL PLAYERS ===")
    print(f"Loaded {len(matcher.separated_players)} separated base names")
    print(f"Loaded {len(matcher.mapped_players)} existing mappings")

    results = []

    for player_name, team_name in test_cases:
        print(f"\nTesting: '{player_name}' from '{team_name}'")

        result = matcher.find_player_match(player_name, team_name)

        print(f"  Action: {result['action']}")
        print(f"  Target: {result['player_name']} (ID: {result['player_id']})")
        print(f"  Confidence: {result['confidence']}%")
        print(f"  Notes: {result['notes']}")

        results.append({
            'input_name': player_name,
            'input_team': team_name,
            'result': result
        })

    # Summary
    print(f"\n=== SUMMARY ===")
    action_counts = {}
    for r in results:
        action = r['result']['action']
        action_counts[action] = action_counts.get(action, 0) + 1

    for action, count in sorted(action_counts.items()):
        print(f"{action}: {count}")

    # Show interesting cases
    print(f"\n=== INTERESTING CASES ===")
    for r in results:
        if r['result']['confidence'] < 100:
            print(f"'{r['input_name']}' + '{r['input_team']}'")
            print(f"  -> {r['result']['action']}: {r['result']['player_name']} ({r['result']['confidence']}%)")

    return results

if __name__ == "__main__":
    # Create backup first
    backup = create_backup()

    try:
        results = test_real_players()

        print(f"\nTest completed successfully with {len(results)} cases tested")

        # Ask if user wants to restore backup
        choice = input("\nRestore backup? (y/N): ").lower()
        if choice == 'y':
            restore_backup(backup)
        else:
            print(f"Backup preserved: {backup}")

    except Exception as e:
        print(f"Error during test: {e}")
        print("Restoring backup...")
        restore_backup(backup)