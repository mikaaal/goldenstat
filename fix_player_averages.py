"""
Fix player averages by correctly calculating with checkout logic.

Handles TWO different checkout data formats from nakka/dartconnect API:
1. Standard format: score = number of darts (1-3), points = previous remaining_score
2. Alternative format: score = points scored (>3), darts_used = number of darts
"""

import sqlite3

def calculate_correct_average(db_path='goldenstat.db'):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    print("=== FIXING PLAYER AVERAGES (BOTH CHECKOUT FORMATS) ===\n")

    # Get all sub_matches
    cursor.execute("SELECT DISTINCT id FROM sub_matches ORDER BY id")
    sub_match_ids = [row[0] for row in cursor.fetchall()]

    print(f"Processing {len(sub_match_ids)} sub-matches...")

    updates = []
    errors = 0
    format_stats = {'standard': 0, 'alternative': 0, 'mixed': 0}

    for sub_match_id in sub_match_ids:
        try:
            # Get all throws for this sub-match
            cursor.execute('''
                SELECT l.leg_number, t.team_number, t.score, t.darts_used, t.remaining_score
                FROM legs l
                JOIN throws t ON t.leg_id = l.id
                WHERE l.sub_match_id = ?
                ORDER BY l.leg_number, t.team_number, t.id
            ''', (sub_match_id,))

            all_throws = cursor.fetchall()

            # Calculate for each team
            team_stats = {1: {'score': 0, 'darts': 0}, 2: {'score': 0, 'darts': 0}}
            last_remaining = {}
            checkout_formats = set()

            for leg_num, team, score, darts_used, remaining in all_throws:
                key = (leg_num, team)

                # Skip starting throw (score=0, remaining=501)
                if score == 0 and remaining == 501:
                    continue

                if remaining == 0:
                    # Checkout throw - detect format based on score value
                    prev_rem = last_remaining.get(key, 0)

                    if score <= 3:
                        # Standard format: score = number of darts, points from prev_remaining
                        checkout_darts = score if score else 3
                        checkout_score = prev_rem
                        checkout_formats.add('standard')
                    else:
                        # Alternative format: score = points scored, darts from darts_used
                        checkout_score = score
                        checkout_darts = darts_used if darts_used else 3
                        checkout_formats.add('alternative')

                    team_stats[team]['score'] += checkout_score
                    team_stats[team]['darts'] += checkout_darts
                else:
                    # Regular throw: count score (if >0) and darts (always)
                    if score > 0:
                        team_stats[team]['score'] += score
                    team_stats[team]['darts'] += (darts_used if darts_used else 3)
                    last_remaining[key] = remaining

            # Track which format(s) this match uses
            if len(checkout_formats) == 2:
                format_stats['mixed'] += 1
            elif 'alternative' in checkout_formats:
                format_stats['alternative'] += 1
            elif 'standard' in checkout_formats:
                format_stats['standard'] += 1

            # Calculate averages and prepare updates
            for team in [1, 2]:
                total_score = team_stats[team]['score']
                total_darts = team_stats[team]['darts']

                if total_darts > 0:
                    avg = round((total_score / total_darts) * 3, 2)
                    updates.append((avg, sub_match_id, team))

        except Exception as e:
            errors += 1
            print(f"Error processing sub_match {sub_match_id}: {e}")

    print(f"\nFormat distribution:")
    print(f"  Standard format (score <= 3): {format_stats['standard']} matches")
    print(f"  Alternative format (score > 3): {format_stats['alternative']} matches")
    print(f"  Mixed formats: {format_stats['mixed']} matches")

    print(f"\nCalculated {len(updates)} averages")
    print(f"Errors: {errors}")

    # Update database
    print("\nUpdating database...")
    cursor.executemany('''
        UPDATE sub_match_participants
        SET player_avg = ?
        WHERE sub_match_id = ? AND team_number = ?
    ''', updates)

    conn.commit()
    print(f"[OK] Updated {cursor.rowcount} player averages")

    # Verify with test cases
    print("\n=== VERIFICATION ===")
    test_cases = [
        (10125, 1, 88.41, "Anton Östlund"),
        (10125, 2, 69.74, "Mats Jansson"),
        (19261, 1, 83.50, "Anton Östlund"),
        (19261, 2, 48.78, "Jonas Fredriksson"),
        (19257, 1, 56.34, "Markus Hoflin"),
        (19257, 2, 62.13, "Martin Koverhult"),
        (2724, 1, 53.44, "Marko K"),
        (2724, 2, 47.77, "Bo Zetterman"),
        (19059, 1, 54.99, "Micke Lundberg"),  # Mixed format (score=3 != prev=76)
        (19059, 2, 41.12, "Marie Åsröm"),
    ]

    for sub_match_id, team, expected_avg, player_name in test_cases:
        cursor.execute('''
            SELECT smp.player_avg, p.name
            FROM sub_match_participants smp
            JOIN players p ON p.id = smp.player_id
            WHERE smp.sub_match_id = ? AND smp.team_number = ?
        ''', (sub_match_id, team))

        result = cursor.fetchone()
        if result:
            actual_avg, actual_name = result
            status = "[OK]" if abs(actual_avg - expected_avg) < 0.02 else "[FAIL]"
            print(f"{status} Sub-match {sub_match_id}, Team {team} ({actual_name}): {actual_avg:.2f} (expected {expected_avg:.2f})")
        else:
            print(f"[FAIL] Sub-match {sub_match_id}, Team {team}: NOT FOUND")

    conn.close()

if __name__ == "__main__":
    calculate_correct_average()
