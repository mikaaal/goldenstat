#!/usr/bin/env python3
"""
Test Mapping Scenarios
Tests different scenarios for player name mapping to validate the algorithm.

Created: 2025-09-22
"""
import sqlite3
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from safe_name_resolver import SafeNameResolver

def test_scenario_analysis():
    """Test various mapping scenarios"""
    resolver = SafeNameResolver()
    
    print("=== Testing Player Name Mapping Scenarios ===\\n")
    
    # Test 1: Check what happens when we have obvious mismatches
    print("1. Analyzing current 'Peter' situation:")
    peter_analysis = resolver.analyze_first_name_mappings("Peter")
    print(f"   Total contexts: {peter_analysis['total_contexts']}")
    print(f"   Context groups: {peter_analysis['context_groups']}")
    print(f"   Can disambiguate: {peter_analysis['can_disambiguate']}")
    
    # Test 2: Look for cases where we might have real mapping opportunities
    print("\\n2. Looking for potential mapping candidates...")
    
    with sqlite3.connect("../goldenstat.db") as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Find short names that might be abbreviations of longer names
        cursor.execute("""
        SELECT 
            short_p.name as short_name,
            short_p.id as short_id,
            long_p.name as long_name, 
            long_p.id as long_id
        FROM players short_p, players long_p
        WHERE LENGTH(short_p.name) <= 10 
            AND LENGTH(long_p.name) > LENGTH(short_p.name)
            AND long_p.name LIKE short_p.name || '%'
            AND short_p.id != long_p.id
        ORDER BY short_p.name, long_p.name
        LIMIT 15
        """)
        
        potential_mappings = cursor.fetchall()
        print(f"   Found {len(potential_mappings)} potential name extension mappings:")
        
        for mapping in potential_mappings:
            print(f"     '{mapping['short_name']}' -> '{mapping['long_name']}'")
            
            # Test if these could be safely mapped
            short_contexts = resolver.get_player_contexts(mapping['short_name'])
            long_contexts = resolver.get_player_contexts(mapping['long_name'])
            
            print(f"       Short name contexts: {len(short_contexts)}")
            print(f"       Long name contexts: {len(long_contexts)}")
            
            # Check for temporal conflicts between the two players
            all_contexts = short_contexts + long_contexts
            conflicts = resolver.detect_temporal_conflicts(all_contexts)
            
            if conflicts:
                print(f"       ⚠ Found {len(conflicts)} temporal conflicts - NOT safe to merge")
            else:
                print(f"       ✓ No temporal conflicts - potentially safe to merge")
            print()
    
    # Test 3: Case variations
    print("\\n3. Looking for case variation candidates...")
    with sqlite3.connect("../goldenstat.db") as conn:
        cursor = conn.cursor()
        
        cursor.execute("""
        SELECT 
            p1.name as name1,
            p1.id as id1,
            p2.name as name2,
            p2.id as id2
        FROM players p1, players p2
        WHERE LOWER(p1.name) = LOWER(p2.name)
            AND p1.name != p2.name
            AND p1.id < p2.id
        LIMIT 10
        """)
        
        case_variations = cursor.fetchall()
        print(f"   Found {len(case_variations)} case variation pairs:")
        
        for pair in case_variations:
            print(f"     '{pair[0]}' vs '{pair[2]}'")
            
            # Test temporal conflicts
            contexts1 = resolver.get_player_contexts(pair[0])
            contexts2 = resolver.get_player_contexts(pair[2])
            all_contexts = contexts1 + contexts2
            conflicts = resolver.detect_temporal_conflicts(all_contexts)
            
            if conflicts:
                print(f"       ⚠ Found temporal conflicts - different players")
            else:
                print(f"       ✓ No conflicts - likely same player, different case")
            print()

def test_peter_specifically():
    """Detailed analysis of the Peter case"""
    print("\\n=== Detailed Peter Analysis ===")
    
    resolver = SafeNameResolver()
    
    # Get all Peter contexts
    contexts = resolver.get_player_contexts("Peter")
    print(f"Found {len(contexts)} contexts for 'Peter':")
    
    for ctx in contexts:
        print(f"  Player ID {ctx.player_id}: {ctx.club_name} ({ctx.division}) {ctx.season}")
        print(f"    Matches: {ctx.match_count}, Period: {ctx.date_start} to {ctx.date_end}")
    
    # Check if any of these Peters might be specific Peters
    print("\\nChecking if any 'Peter' contexts match full Peter names...")
    
    with sqlite3.connect("../goldenstat.db") as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
        SELECT name, id FROM players 
        WHERE name LIKE 'Peter %' 
        ORDER BY name
        """)
        
        full_peters = cursor.fetchall()
        print(f"Found {len(full_peters)} full Peter names in database")
        
        for peter in full_peters[:5]:  # Show first 5
            peter_contexts = resolver.get_player_contexts(peter['name'])
            print(f"\\n  {peter['name']} (ID: {peter['id']}):")
            print(f"    Contexts: {len(peter_contexts)}")
            
            for ctx in peter_contexts:
                print(f"      {ctx.club_name} ({ctx.division}) {ctx.season} - {ctx.match_count} matches")

if __name__ == "__main__":
    test_scenario_analysis()
    test_peter_specifically()