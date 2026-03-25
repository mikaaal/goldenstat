"""Fix swapped side_number in throws and winner_side/first_side in legs.

About 36% of cup matches had detail data fetched with a reversed tmid,
causing side 1/2 to be swapped in throws and legs. The stored p1_average
and p2_average (from the API summary) are correct, so we detect affected
matches by comparing stored averages against averages calculated from throws.
"""
import sqlite3
import sys

DB_PATH = sys.argv[1] if len(sys.argv) > 1 else 'cups.db'


def main():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    # Find all matches with detail + both averages set
    c.execute("""
        SELECT id, p1_average, p2_average
        FROM cup_matches
        WHERE has_detail = 1 AND p1_average > 0 AND p2_average > 0
    """)
    matches = c.fetchall()
    print(f"Checking {len(matches)} matches...")

    swapped_ids = []
    for m in matches:
        mid = m['id']
        c.execute("""
            SELECT th.side_number,
                   CAST(SUM(th.score) AS REAL) / SUM(CASE WHEN th.darts_used IS NOT NULL THEN th.darts_used ELSE 3 END) * 3
            FROM throws th
            JOIN legs l ON th.leg_id = l.id
            WHERE l.cup_match_id = ?
            GROUP BY th.side_number
        """, (mid,))
        avgs = {r[0]: r[1] for r in c.fetchall()}
        if 1 not in avgs or 2 not in avgs:
            continue

        stored_ok = abs(m['p1_average'] - avgs[1]) < 0.5
        stored_swapped = abs(m['p1_average'] - avgs[2]) < 0.5 and abs(m['p2_average'] - avgs[1]) < 0.5

        if stored_swapped and not stored_ok:
            swapped_ids.append(mid)

    print(f"Found {len(swapped_ids)} matches with swapped sides.")

    if not swapped_ids:
        print("Nothing to fix.")
        conn.close()
        return

    # Fix in batches
    batch_size = 500
    for i in range(0, len(swapped_ids), batch_size):
        batch = swapped_ids[i:i + batch_size]
        placeholders = ','.join('?' * len(batch))

        # Swap side_number in throws: 1->2, 2->1
        c.execute(f"""
            UPDATE throws SET side_number = 3 - side_number
            WHERE leg_id IN (
                SELECT l.id FROM legs l WHERE l.cup_match_id IN ({placeholders})
            )
        """, batch)

        # Swap winner_side and first_side in legs
        c.execute(f"""
            UPDATE legs SET winner_side = 3 - winner_side, first_side = 3 - first_side
            WHERE cup_match_id IN ({placeholders})
        """, batch)

        conn.commit()
        print(f"  Fixed batch {i // batch_size + 1} ({len(batch)} matches)")

    # Verify
    print("\nVerifying...")
    sample = swapped_ids[:100]
    fixed = 0
    for mid in sample:
        c.execute("""
            SELECT th.side_number,
                   CAST(SUM(th.score) AS REAL) / SUM(CASE WHEN th.darts_used IS NOT NULL THEN th.darts_used ELSE 3 END) * 3
            FROM throws th
            JOIN legs l ON th.leg_id = l.id
            WHERE l.cup_match_id = ?
            GROUP BY th.side_number
        """, (mid,))
        avgs = {r[0]: r[1] for r in c.fetchall()}
        c.execute("SELECT p1_average FROM cup_matches WHERE id = ?", (mid,))
        stored = c.fetchone()[0]
        if 1 in avgs and abs(stored - avgs[1]) < 0.5:
            fixed += 1

    print(f"Verification: {fixed}/{len(sample)} sample matches now correct.")
    conn.close()


if __name__ == '__main__':
    main()
