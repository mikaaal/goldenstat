#!/usr/bin/env python3
import sqlite3

def test_team_lookup():
    with sqlite3.connect("goldenstat.db") as conn:
        cursor = conn.cursor()

        # Test the exact query that should run for AIK (1A)
        base_team_name = "AIK"
        division_from_name = "1A"

        print(f"Testing lookup for: {base_team_name} with division {division_from_name}")

        # First try exact match
        team_name_with_division = f"{base_team_name} ({division_from_name})"
        print(f"Trying exact match: '{team_name_with_division}'")
        cursor.execute("SELECT id, name FROM teams WHERE name = ?", (team_name_with_division,))
        result = cursor.fetchone()
        if result:
            print(f"  Found: {result}")
        else:
            print("  Not found")

        # Try fallback query
        print(f"Trying fallback query: LIKE '{base_team_name}%' AND LIKE '%({division_from_name})'")
        cursor.execute("SELECT name FROM teams WHERE name LIKE ? AND name LIKE ?",
                     (f"{base_team_name}%", f"%({division_from_name})"))
        potential_matches = cursor.fetchall()
        print(f"  Found {len(potential_matches)} matches:")
        for match in potential_matches:
            print(f"    '{match[0]}'")

if __name__ == "__main__":
    test_team_lookup()