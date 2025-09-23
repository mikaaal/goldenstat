#!/usr/bin/env python3
import sqlite3

def debug_team_lookup():
    with sqlite3.connect("goldenstat.db") as conn:
        cursor = conn.cursor()

        # Look for AIK teams
        print("Searching for AIK teams...")
        cursor.execute("SELECT name FROM teams WHERE name LIKE '%AIK%' ORDER BY name")
        aik_teams = cursor.fetchall()

        print(f"Found {len(aik_teams)} AIK teams:")
        for team in aik_teams:
            print(f"  '{team[0]}'")

        # Look for 3FA division teams
        print("\nSearching for 3FA teams...")
        cursor.execute("SELECT name FROM teams WHERE name LIKE '%3FA%' ORDER BY name")
        three_fa_teams = cursor.fetchall()

        print(f"Found {len(three_fa_teams)} 3FA teams:")
        for team in three_fa_teams:
            print(f"  '{team[0]}'")

        # Look for specific AIK divisions
        divisions = ["1A", "2A", "3FA"]
        for div in divisions:
            print(f"\nSearching for AIK teams in division '{div}'...")
            cursor.execute("SELECT DISTINCT name FROM teams WHERE name LIKE ? AND name LIKE ? ORDER BY name", (f"AIK%", f"%{div}%"))
            results = cursor.fetchall()
            print(f"Found {len(results)} AIK {div} teams:")
            for team in results:
                print(f"  '{team[0]}'")

if __name__ == "__main__":
    debug_team_lookup()