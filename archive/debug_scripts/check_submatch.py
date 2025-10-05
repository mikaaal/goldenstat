import sqlite3

conn = sqlite3.connect('goldenstat.db')
cursor = conn.cursor()

# Get all legs with dart counts
cursor.execute('''
    SELECT
        l.leg_number,
        l.id as leg_id,
        l.winner_team,
        SUM(CASE WHEN t.darts_used IS NOT NULL THEN t.darts_used ELSE 3 END) as total_darts
    FROM legs l
    JOIN throws t ON l.id = t.leg_id AND t.team_number = l.winner_team
    WHERE l.sub_match_id = 10125
    GROUP BY l.leg_number, l.id, l.winner_team
    ORDER BY l.leg_number
''')

legs = cursor.fetchall()
print("All legs in sub_match 10125:")
print()

for leg_num, leg_id, winner, total_darts in legs:
    print(f"Leg {leg_num} (id={leg_id}, winner=team {winner}): {total_darts} pilar")

    # Show throws for this leg
    cursor.execute('''
        SELECT round_number, score, remaining_score, darts_used
        FROM throws
        WHERE leg_id = ? AND team_number = ?
        ORDER BY round_number
    ''', (leg_id, winner))

    throws = cursor.fetchall()
    for rnd, score, remaining, darts in throws:
        darts_used = darts if darts is not None else 3
        print(f"  Round {rnd}: {score} pts, {remaining} left, {darts_used} darts")
    print()

conn.close()
