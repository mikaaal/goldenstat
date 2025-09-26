#!/usr/bin/env python3
"""
Fixa felaktiga player averages som inte matchar team averages
"""
import sqlite3

def fix_player_averages():
    """Fixa player averages för att matcha korrekta team averages"""
    print("=== FIXAR PLAYER AVERAGES ===")

    with sqlite3.connect("goldenstat.db") as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Hitta alla sub_matches där participant averages inte matchar team averages
        cursor.execute("""
            SELECT sm.id, sm.team1_avg, sm.team2_avg,
                   COUNT(CASE WHEN smp.team_number = 1 AND ABS(smp.player_avg - sm.team1_avg) > 0.01 THEN 1 END) as team1_mismatches,
                   COUNT(CASE WHEN smp.team_number = 2 AND ABS(smp.player_avg - sm.team2_avg) > 0.01 THEN 1 END) as team2_mismatches
            FROM sub_matches sm
            JOIN matches m ON sm.match_id = m.id
            JOIN sub_match_participants smp ON sm.id = smp.sub_match_id
            WHERE m.season IN ('2024/2025', '2025/2026')
            GROUP BY sm.id, sm.team1_avg, sm.team2_avg
            HAVING team1_mismatches > 0 OR team2_mismatches > 0
            ORDER BY sm.id
        """)

        problematic_subs = cursor.fetchall()
        print(f"Hittade {len(problematic_subs)} sub_matches med felaktiga player averages")

        fixes_applied = 0

        for sub in problematic_subs:
            sub_match_id = sub['id']
            team1_avg = sub['team1_avg']
            team2_avg = sub['team2_avg']

            print(f"\nFixar sub_match {sub_match_id}:")
            print(f"  Korrekt team1_avg: {team1_avg}")
            print(f"  Korrekt team2_avg: {team2_avg}")
            print(f"  Team1 mismatches: {sub['team1_mismatches']}")
            print(f"  Team2 mismatches: {sub['team2_mismatches']}")

            # Uppdatera team 1 players
            cursor.execute("""
                UPDATE sub_match_participants
                SET player_avg = ?
                WHERE sub_match_id = ? AND team_number = 1
            """, (team1_avg, sub_match_id))

            team1_updated = cursor.rowcount

            # Uppdatera team 2 players
            cursor.execute("""
                UPDATE sub_match_participants
                SET player_avg = ?
                WHERE sub_match_id = ? AND team_number = 2
            """, (team2_avg, sub_match_id))

            team2_updated = cursor.rowcount

            print(f"  Uppdaterade {team1_updated} spelare i team 1")
            print(f"  Uppdaterade {team2_updated} spelare i team 2")

            fixes_applied += 1

        conn.commit()
        print(f"\n[OK] Fixade player averages i {fixes_applied} sub_matches")

        # Verifiera fix för de specifika sub_matches som nämndes
        print("\n=== VERIFIERING ===")
        for sub_match_id in [8321, 8322]:
            cursor.execute("""
                SELECT sm.id, sm.team1_avg, sm.team2_avg,
                       smp.team_number, smp.player_avg, p.name
                FROM sub_matches sm
                JOIN sub_match_participants smp ON sm.id = smp.sub_match_id
                JOIN players p ON smp.player_id = p.id
                WHERE sm.id = ?
                ORDER BY smp.team_number, p.name
            """, (sub_match_id,))

            results = cursor.fetchall()
            if results:
                print(f"\nSub_match {sub_match_id}:")
                for row in results:
                    expected_avg = row['team1_avg'] if row['team_number'] == 1 else row['team2_avg']
                    status = "OK" if abs(row['player_avg'] - expected_avg) < 0.01 else "FAIL"
                    print(f"  {row['name']} (team {row['team_number']}): {row['player_avg']} (förväntat: {expected_avg}) [{status}]")

if __name__ == "__main__":
    fix_player_averages()