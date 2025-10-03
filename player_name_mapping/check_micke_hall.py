#!/usr/bin/env python3
import sqlite3

conn = sqlite3.connect('goldenstat.db')
cursor = conn.cursor()

cursor.execute('SELECT id, name FROM players WHERE name LIKE "%Micke H%" ORDER BY name')
players = cursor.fetchall()

print('Micke H-spelare:\n')
for p_id, p_name in players:
    print(f'  ID {p_id}: {p_name}')

print()

for p_id, p_name in players:
    cursor.execute('SELECT COUNT(*) FROM sub_match_participants WHERE player_id = ?', (p_id,))
    matches = cursor.fetchone()[0]

    cursor.execute('SELECT COUNT(*) FROM sub_match_player_mappings WHERE original_player_id = ?', (p_id,))
    mappings_from = cursor.fetchone()[0]

    cursor.execute('SELECT COUNT(*) FROM sub_match_player_mappings WHERE correct_player_id = ?', (p_id,))
    mappings_to = cursor.fetchone()[0]

    print(f'{p_name}:')
    print(f'  {matches} matcher direkt')
    print(f'  {mappings_from} mappningar FROM (där denna är original)')
    print(f'  {mappings_to} mappningar TO (där denna är correct)')
    print()
