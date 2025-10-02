#!/usr/bin/env python3
"""
Check for duplicate participants in sub_match_participants.
This can happen when both the base player and mapped player have entries for the same sub-match.
"""
import sqlite3

def check_duplicates():
    with sqlite3.connect("goldenstat.db") as conn:
        cursor = conn.cursor()

        # Find sub-matches that have duplicate participants
        # (same sub_match + team_number, but different players)
        cursor.execute('''
            SELECT
                smp1.sub_match_id,
                smp1.team_number,
                smp1.player_id as player1_id,
                p1.name as player1_name,
                smp2.player_id as player2_id,
                p2.name as player2_name,
                smpm.correct_player_id,
                p3.name as correct_name
            FROM sub_match_participants smp1
            JOIN sub_match_participants smp2 ON
                smp1.sub_match_id = smp2.sub_match_id AND
                smp1.team_number = smp2.team_number AND
                smp1.player_id < smp2.player_id
            JOIN players p1 ON smp1.player_id = p1.id
            JOIN players p2 ON smp2.player_id = p2.id
            LEFT JOIN sub_match_player_mappings smpm ON
                smp1.sub_match_id = smpm.sub_match_id AND
                (smp1.player_id = smpm.original_player_id OR smp2.player_id = smpm.original_player_id)
            LEFT JOIN players p3 ON smpm.correct_player_id = p3.id
            WHERE smpm.sub_match_id IS NOT NULL
            ORDER BY smp1.sub_match_id
        ''')

        duplicates = cursor.fetchall()

        if duplicates:
            print(f"=== Found {len(duplicates)} potential duplicate participants ===\n")

            for dup in duplicates[:20]:
                sub_match_id, team_num, p1_id, p1_name, p2_id, p2_name, correct_id, correct_name = dup
                print(f"Sub-match {sub_match_id}, Team {team_num}:")
                print(f"  Player 1: {p1_name} (ID {p1_id})")
                print(f"  Player 2: {p2_name} (ID {p2_id})")
                print(f"  Should be: {correct_name} (ID {correct_id})")
                print()

            if len(duplicates) > 20:
                print(f"... and {len(duplicates) - 20} more duplicates")
        else:
            print("No duplicate participants found where mapping exists!")

        # Also check for potential duplicates even without mapping
        # (same sub_match + team_number, multiple players from same "family")
        cursor.execute('''
            SELECT
                smp.sub_match_id,
                smp.team_number,
                COUNT(DISTINCT smp.player_id) as player_count,
                GROUP_CONCAT(DISTINCT p.name) as player_names,
                GROUP_CONCAT(DISTINCT smp.player_id) as player_ids
            FROM sub_match_participants smp
            JOIN players p ON smp.player_id = p.id
            GROUP BY smp.sub_match_id, smp.team_number
            HAVING player_count > 2
            ORDER BY player_count DESC
            LIMIT 10
        ''')

        multi_players = cursor.fetchall()

        if multi_players:
            print(f"\n=== Sub-matches with more than 2 players per team ===\n")
            for row in multi_players:
                sub_match_id, team_num, count, names, ids = row
                print(f"Sub-match {sub_match_id}, Team {team_num}: {count} players")
                print(f"  Players: {names}")
                print()

if __name__ == "__main__":
    check_duplicates()
