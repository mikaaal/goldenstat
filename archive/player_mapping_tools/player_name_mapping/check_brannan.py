#!/usr/bin/env python3
import sqlite3

conn = sqlite3.connect('goldenstat.db')
cursor = conn.cursor()

cursor.execute('SELECT id, name FROM players WHERE name LIKE "%Brännan%"')
players = cursor.fetchall()

print('Brännan-spelare:')
for p_id, p_name in players:
    print(f'  ID {p_id}: {p_name}')

print()

for p_id, p_name in players:
    cursor.execute('SELECT COUNT(*) FROM sub_match_participants WHERE player_id = ?', (p_id,))
    matches = cursor.fetchone()[0]

    cursor.execute('SELECT COUNT(*) FROM sub_match_player_mappings WHERE original_player_id = ?', (p_id,))
    mappings = cursor.fetchone()[0]

    print(f'{p_name}: {matches} matcher, {mappings} mappningar')
