import sqlite3

conn = sqlite3.connect('goldenstat.db')
cursor = conn.cursor()

query = '''
SELECT
    p.name,
    prev.remaining_score as checkout,
    CASE WHEN smp.team_number = 1 THEN t1.name ELSE t2.name END as team_name,
    CASE WHEN smp.team_number = 1 THEN t2.name ELSE t1.name END as opponent_name,
    DATE(m.match_date) as match_date,
    sm.id as sub_match_id,
    l.id as leg_id,
    curr.round_number
FROM throws curr
JOIN throws prev ON curr.leg_id = prev.leg_id
    AND curr.team_number = prev.team_number
    AND prev.round_number = curr.round_number - 1
JOIN legs l ON curr.leg_id = l.id
JOIN sub_matches sm ON l.sub_match_id = sm.id
JOIN matches m ON sm.match_id = m.id
JOIN teams t1 ON m.team1_id = t1.id
JOIN teams t2 ON m.team2_id = t2.id
JOIN sub_match_participants smp ON sm.id = smp.sub_match_id
    AND smp.team_number = curr.team_number
JOIN players p ON smp.player_id = p.id
WHERE curr.remaining_score = 0
    AND prev.remaining_score > 0
    AND curr.team_number = l.winner_team
    AND sm.match_type = 'Singles'
    AND p.name = 'Tommy Pilblad'
    AND prev.remaining_score = 170
ORDER BY prev.remaining_score DESC
'''

rows = cursor.execute(query).fetchall()
for row in rows:
    print(row)

conn.close()
