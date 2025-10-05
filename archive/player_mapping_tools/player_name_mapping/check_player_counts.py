#!/usr/bin/env python3
"""
Check for sub-matches with incorrect number of players.
Singles should have 2 players (1 per team)
Doubles should have 4 players (2 per team)
"""
import sqlite3

def check_player_counts():
    with sqlite3.connect("goldenstat.db") as conn:
        cursor = conn.cursor()

        # Find sub-matches with wrong player count
        cursor.execute('''
            SELECT
                sm.id,
                sm.match_type,
                COUNT(DISTINCT smp.player_id) as player_count,
                GROUP_CONCAT(DISTINCT p.name) as players
            FROM sub_matches sm
            JOIN sub_match_participants smp ON sm.id = smp.sub_match_id
            JOIN players p ON smp.player_id = p.id
            GROUP BY sm.id
            HAVING
                (sm.match_type = 'Singles' AND player_count != 2) OR
                (sm.match_type = 'Doubles' AND player_count != 4)
            ORDER BY player_count DESC
            LIMIT 50
        ''')

        wrong_counts = cursor.fetchall()

        if wrong_counts:
            print(f"=== Found {len(wrong_counts)} sub-matches with wrong player count ===\n")

            for sm_id, match_type, count, players in wrong_counts:
                expected = 2 if match_type == 'Singles' else 4
                print(f"Sub-match {sm_id} ({match_type}): {count} players (expected {expected})")
                print(f"  Players: {players[:100]}")
                print()
        else:
            print("All sub-matches have correct player counts!")

        # Count totals
        cursor.execute('''
            SELECT COUNT(*)
            FROM sub_matches sm
            JOIN (
                SELECT sub_match_id, COUNT(DISTINCT player_id) as cnt
                FROM sub_match_participants
                GROUP BY sub_match_id
            ) smp ON sm.id = smp.sub_match_id
            WHERE
                (sm.match_type = 'Singles' AND smp.cnt != 2) OR
                (sm.match_type = 'Doubles' AND smp.cnt != 4)
        ''')

        total = cursor.fetchone()[0]
        print(f"\nTotal sub-matches with wrong player count: {total}")

        # Check for sub-matches with too many players per team
        cursor.execute('''
            SELECT
                sm.id,
                sm.match_type,
                smp.team_number,
                COUNT(DISTINCT smp.player_id) as players_in_team,
                GROUP_CONCAT(DISTINCT p.name) as player_names
            FROM sub_matches sm
            JOIN sub_match_participants smp ON sm.id = smp.sub_match_id
            JOIN players p ON smp.player_id = p.id
            GROUP BY sm.id, smp.team_number
            HAVING
                (sm.match_type = 'Singles' AND players_in_team > 1) OR
                (sm.match_type = 'Doubles' AND players_in_team > 2)
            ORDER BY players_in_team DESC
            LIMIT 20
        ''')

        too_many_per_team = cursor.fetchall()

        if too_many_per_team:
            print(f"\n=== Sub-matches with too many players per team ===\n")
            for sm_id, match_type, team_num, count, players in too_many_per_team:
                expected = 1 if match_type == 'Singles' else 2
                print(f"Sub-match {sm_id} ({match_type}), Team {team_num}: {count} players (expected {expected})")
                print(f"  Players: {players}")
                print()

if __name__ == "__main__":
    check_player_counts()
