#!/usr/bin/env python3
"""
Testa att den fixade import-logiken inte skapar dubbletter
"""
import sqlite3

def test_no_duplicate_participants():
    """Testa att det inte finns dublettspelare i samma matcher"""
    print("=== TESTAR DUBLETTSKYDD ===")

    with sqlite3.connect('goldenstat.db') as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Hitta alla fall där samma basnamn finns i samma sub_match
        cursor.execute('''
            SELECT sm.id as sub_match_id,
                   p1.name as name1, p1.id as id1,
                   p2.name as name2, p2.id as id2,
                   m.match_date, t1.name as team1, t2.name as team2
            FROM sub_matches sm
            JOIN sub_match_participants smp1 ON sm.id = smp1.sub_match_id
            JOIN sub_match_participants smp2 ON sm.id = smp2.sub_match_id AND smp1.player_id != smp2.player_id
            JOIN players p1 ON smp1.player_id = p1.id
            JOIN players p2 ON smp2.player_id = p2.id
            JOIN matches m ON sm.match_id = m.id
            JOIN teams t1 ON m.team1_id = t1.id
            JOIN teams t2 ON m.team2_id = t2.id
            WHERE (
                (p1.name LIKE '%(%' AND p2.name NOT LIKE '%(%'
                 AND p2.name = TRIM(SUBSTR(p1.name, 1, INSTR(p1.name, '(') - 1)))
                OR
                (p2.name LIKE '%(%' AND p1.name NOT LIKE '%(%'
                 AND p1.name = TRIM(SUBSTR(p2.name, 1, INSTR(p2.name, '(') - 1)))
            )
            AND m.season = '2025/2026'
            ORDER BY sm.id
        ''')

        duplicates = cursor.fetchall()

        if duplicates:
            print(f"[ERROR] HITTADE {len(duplicates)} DUBLETTER I 2025/2026:")
            for dup in duplicates:
                print(f"  Sub_match {dup['sub_match_id']}: {dup['name1']} vs {dup['name2']}")
                print(f"    Match: {dup['team1']} vs {dup['team2']} ({dup['match_date'][:10]})")
        else:
            print("[OK] INGA DUBLETTER HITTADE I 2025/2026!")

        # Kolla total statistik
        cursor.execute('''
            SELECT COUNT(DISTINCT smp.sub_match_id) as total_sub_matches,
                   COUNT(*) as total_participants
            FROM sub_match_participants smp
            JOIN sub_matches sm ON smp.sub_match_id = sm.id
            JOIN matches m ON sm.match_id = m.id
            WHERE m.season = '2025/2026'
        ''')

        stats = cursor.fetchone()
        print(f"\\n[STATS] 2025/2026 STATISTIK:")
        print(f"  Sub_matches: {stats['total_sub_matches']}")
        print(f"  Participants: {stats['total_participants']}")

        return len(duplicates) == 0

if __name__ == "__main__":
    test_no_duplicate_participants()