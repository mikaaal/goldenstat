#!/usr/bin/env python3
"""
Debug mappings to see what's happening
"""
import sqlite3
import sys
sys.path.append('..')
from app import get_effective_player_ids

def debug_peter_mappings():
    with sqlite3.connect("../goldenstat.db") as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        print("=== All mappings in database ===")
        cursor.execute("""
            SELECT pnm.*, p_source.name as source_name, p_target.name as target_name 
            FROM player_name_mappings pnm 
            JOIN players p_source ON pnm.source_player_id = p_source.id 
            JOIN players p_target ON pnm.target_player_id = p_target.id
        """)
        
        mappings = cursor.fetchall()
        print(f"Found {len(mappings)} mappings:")
        for mapping in mappings:
            print(f"  {mapping['source_name']} -> {mapping['target_name']} (confidence: {mapping['confidence']})")
        
        print("\n=== Testing get_effective_player_ids function ===")
        test_names = ["Peter", "Peter Söron", "Peter Book", "Peter Ekman"]
        
        for name in test_names:
            player_ids = get_effective_player_ids(cursor, name)
            print(f"{name}: {player_ids}")
            
            # Get player names for these IDs
            if player_ids:
                placeholders = ','.join(['?'] * len(player_ids))
                cursor.execute(f"SELECT id, name FROM players WHERE id IN ({placeholders})", player_ids)
                players = cursor.fetchall()
                names = [p['name'] for p in players]
                print(f"  -> Player names: {names}")
        
        print("\n=== Direct Peter match count ===")
        cursor.execute("SELECT COUNT(*) FROM sub_match_participants WHERE player_id = 386")
        direct_peter_matches = cursor.fetchone()[0]
        print(f"Direct 'Peter' matches: {direct_peter_matches}")
        
        print("\n=== Peter Söron match count ===")
        cursor.execute("SELECT COUNT(*) FROM sub_match_participants WHERE player_id = 838")
        peter_soron_matches = cursor.fetchone()[0]
        print(f"Direct 'Peter Söron' matches: {peter_soron_matches}")

if __name__ == "__main__":
    debug_peter_mappings()