#!/usr/bin/env python3
"""
Verify that all mappings are correct before applying them.
Check that we're not mapping players incorrectly.
"""
import sqlite3

def verify_mappings():
    with sqlite3.connect("goldenstat.db") as conn:
        cursor = conn.cursor()

        print("=== VERIFYING MAPPING CORRECTNESS ===\n")

        issues = []

        # 1. Check that mapped players exist
        print("1. Checking that all correct_player_id exist...")
        cursor.execute('''
            SELECT DISTINCT smpm.correct_player_id, smpm.correct_player_name
            FROM sub_match_player_mappings smpm
            LEFT JOIN players p ON smpm.correct_player_id = p.id
            WHERE p.id IS NULL
        ''')
        missing_players = cursor.fetchall()
        if missing_players:
            print(f"   ERROR: {len(missing_players)} mappings point to non-existent players:")
            for player_id, player_name in missing_players[:5]:
                print(f"     - {player_name} (ID {player_id})")
            issues.append(f"Missing players: {len(missing_players)}")
        else:
            print("   OK: All correct_player_id exist")

        # 2. Check that original players exist
        print("\n2. Checking that all original_player_id exist...")
        cursor.execute('''
            SELECT DISTINCT smpm.original_player_id, p.name
            FROM sub_match_player_mappings smpm
            LEFT JOIN players p ON smpm.original_player_id = p.id
            WHERE p.id IS NULL
        ''')
        missing_originals = cursor.fetchall()
        if missing_originals:
            print(f"   ERROR: {len(missing_originals)} mappings reference non-existent original players")
            issues.append(f"Missing original players: {len(missing_originals)}")
        else:
            print("   OK: All original_player_id exist")

        # 3. Check for mappings to the same player (should not happen)
        print("\n3. Checking for self-mappings (original == correct)...")
        cursor.execute('''
            SELECT COUNT(*)
            FROM sub_match_player_mappings
            WHERE original_player_id = correct_player_id
        ''')
        self_mappings = cursor.fetchone()[0]
        if self_mappings > 0:
            print(f"   ERROR: {self_mappings} mappings map a player to themselves")
            issues.append(f"Self-mappings: {self_mappings}")
        else:
            print("   OK: No self-mappings")

        # 4. Check for conflicting mappings (same sub_match/original mapped to different players)
        print("\n4. Checking for conflicting mappings...")
        cursor.execute('''
            SELECT
                sub_match_id,
                original_player_id,
                COUNT(DISTINCT correct_player_id) as num_targets
            FROM sub_match_player_mappings
            GROUP BY sub_match_id, original_player_id
            HAVING num_targets > 1
        ''')
        conflicts = cursor.fetchall()
        if conflicts:
            print(f"   ERROR: {len(conflicts)} sub-matches have conflicting mappings:")
            for sm_id, orig_id, num in conflicts[:5]:
                cursor.execute('''
                    SELECT p1.name, GROUP_CONCAT(p2.name)
                    FROM sub_match_player_mappings smpm
                    JOIN players p1 ON smpm.original_player_id = p1.id
                    JOIN players p2 ON smpm.correct_player_id = p2.id
                    WHERE smpm.sub_match_id = ? AND smpm.original_player_id = ?
                ''', (sm_id, orig_id))
                orig_name, targets = cursor.fetchone()
                print(f"     Sub-match {sm_id}: {orig_name} -> {targets}")
            issues.append(f"Conflicting mappings: {len(conflicts)}")
        else:
            print("   OK: No conflicting mappings")

        # 5. Sample check: verify a few mappings make sense
        print("\n5. Sample verification of mappings...")
        cursor.execute('''
            SELECT
                smpm.sub_match_id,
                p1.name as original_name,
                p2.name as correct_name,
                smpm.match_context,
                m.season,
                CASE WHEN smp.team_number = 1 THEN t1.name ELSE t2.name END as team_name
            FROM sub_match_player_mappings smpm
            JOIN players p1 ON smpm.original_player_id = p1.id
            JOIN players p2 ON smpm.correct_player_id = p2.id
            JOIN sub_matches sm ON smpm.sub_match_id = sm.id
            JOIN matches m ON sm.match_id = m.id
            JOIN teams t1 ON m.team1_id = t1.id
            JOIN teams t2 ON m.team2_id = t2.id
            JOIN sub_match_participants smp ON sm.id = smp.sub_match_id AND smp.player_id = smpm.original_player_id
            ORDER BY RANDOM()
            LIMIT 10
        ''')
        samples = cursor.fetchall()

        print("\n   Sample mappings:")
        for sm_id, orig, correct, context, season, team in samples:
            # Extract club from correct player name if it has (Club) format
            club_in_name = None
            if '(' in correct and ')' in correct:
                club_in_name = correct.split('(')[1].split(')')[0]

            # Extract club from team name
            team_club = team.split('(')[0].strip() if '(' in team else team

            match = "MATCH" if club_in_name and club_in_name.lower() in team_club.lower() else "CHECK"
            print(f"   [{match}] {orig} -> {correct}")
            print(f"         Context: {context}, Team: {team}")

        # 6. Check that we won't create duplicates
        print("\n6. Checking if applying mappings will create new duplicates...")
        cursor.execute('''
            SELECT
                smpm.sub_match_id,
                smpm.correct_player_id,
                smp.team_number,
                p.name
            FROM sub_match_player_mappings smpm
            JOIN sub_match_participants smp ON
                smpm.sub_match_id = smp.sub_match_id AND
                smpm.original_player_id != smp.player_id
            JOIN players p ON smp.player_id = p.id
            WHERE smp.player_id = smpm.correct_player_id
            LIMIT 10
        ''')
        potential_dups = cursor.fetchall()
        if potential_dups:
            print(f"   WARNING: Found cases where correct player already exists")
            print(f"   (These should be handled by duplicate removal step)")
        else:
            print("   OK: No duplicate issues detected")

        # Summary
        print("\n" + "="*60)
        if issues:
            print("VERIFICATION FAILED - Found issues:")
            for issue in issues:
                print(f"  - {issue}")
            print("\nDO NOT apply mappings until these issues are resolved!")
            return False
        else:
            print("VERIFICATION PASSED - Mappings appear correct")
            print("Safe to apply mappings")
            return True

if __name__ == "__main__":
    verify_mappings()
