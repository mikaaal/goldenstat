#!/usr/bin/env python3
"""
Find Mapping Issues
Systematically check for places where player names are shown incorrectly.

Created: 2025-09-22
"""
import sqlite3
import requests
import json

def test_sub_match_display():
    """Test if sub-matches show correct player names"""
    print("=== Testing Sub-Match Display ===")
    
    # Find a sub-match that should have a mapped player
    with sqlite3.connect("../goldenstat.db") as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Get a sub-match with a mapping
        cursor.execute("""
            SELECT DISTINCT 
                smpm.sub_match_id,
                smpm.original_player_id,
                smpm.correct_player_name,
                p.name as original_name
            FROM sub_match_player_mappings smpm
            JOIN players p ON smpm.original_player_id = p.id
            LIMIT 5
        """)
        
        test_cases = cursor.fetchall()
        
        for case in test_cases:
            sub_match_id = case['sub_match_id']
            expected_name = case['correct_player_name']
            original_name = case['original_name']
            
            print(f"\\nTesting sub-match {sub_match_id}:")
            print(f"  Should show: {expected_name}")
            print(f"  Instead of: {original_name}")
            
            # Test the API
            try:
                response = requests.get(f"http://localhost:3000/api/sub_match/{sub_match_id}")
                if response.status_code == 200:
                    data = response.json()
                    
                    # Check both teams
                    found_correct = False
                    found_incorrect = False
                    
                    for team_key in ['team1_players', 'team2_players']:
                        if team_key in data:
                            for player in data[team_key]:
                                if player['name'] == expected_name:
                                    found_correct = True
                                    print(f"  ✓ Found correct name: {expected_name}")
                                elif player['name'] == original_name:
                                    found_incorrect = True
                                    print(f"  ✗ Found incorrect name: {original_name}")
                    
                    if not found_correct and not found_incorrect:
                        print(f"  ? Neither name found (might be different team)")
                        
                else:
                    print(f"  Error: API returned {response.status_code}")
                    
            except Exception as e:
                print(f"  Error: {e}")

def test_player_stats_display():
    """Test if player stats show correct opponent names"""
    print("\\n=== Testing Player Stats Display ===")
    
    # Test a few mapped players
    test_players = [
        "Johan (Tyresö)",
        "Johan (Rockhangers)", 
        "Johan (Oasen)",
        "Peter Söron"
    ]
    
    for player_name in test_players:
        print(f"\\nTesting {player_name}:")
        
        try:
            response = requests.get(f"http://localhost:3000/api/player/{player_name}")
            if response.status_code == 200:
                data = response.json()
                
                if 'recent_matches' in data and data['recent_matches']:
                    # Check first few matches for opponent names
                    for i, match in enumerate(data['recent_matches'][:3]):
                        opponent = match.get('opponent', 'None')
                        print(f"  Match {i+1}: vs {opponent}")
                        
                        # Check if opponent contains just first names that might be wrong
                        if any(name in opponent for name in ['Johan', 'Peter', 'Jonas']):
                            print(f"    ⚠ Potential mapping issue: {opponent}")
                else:
                    print(f"  No recent matches found")
                    
            else:
                print(f"  Error: API returned {response.status_code}")
                
        except Exception as e:
            print(f"  Error: {e}")

def find_unmapped_first_names():
    """Find first-name players that still have many matches"""
    print("\\n=== Finding Remaining First-Name Issues ===")
    
    with sqlite3.connect("../goldenstat.db") as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Find first-name players with significant match counts
        cursor.execute("""
            SELECT 
                p.id,
                p.name,
                COUNT(DISTINCT smp.sub_match_id) as direct_matches,
                COALESCE(mapped.mapped_away, 0) as mapped_away,
                COUNT(DISTINCT smp.sub_match_id) - COALESCE(mapped.mapped_away, 0) as remaining_matches
            FROM players p
            JOIN sub_match_participants smp ON p.id = smp.player_id
            LEFT JOIN (
                SELECT 
                    original_player_id,
                    COUNT(*) as mapped_away
                FROM sub_match_player_mappings
                GROUP BY original_player_id
            ) mapped ON p.id = mapped.original_player_id
            WHERE LENGTH(p.name) <= 15
                AND p.name NOT LIKE '% %'
                AND p.name NOT LIKE '%(%'
                AND p.name NOT LIKE '%.%'
                AND LENGTH(p.name) >= 3
            GROUP BY p.id, p.name, mapped.mapped_away
            HAVING remaining_matches >= 10
            ORDER BY remaining_matches DESC
        """)
        
        remaining_issues = cursor.fetchall()
        
        print(f"Found {len(remaining_issues)} first-name players with 10+ remaining matches:")
        
        for issue in remaining_issues[:10]:
            print(f"  {issue['name']}: {issue['remaining_matches']} matches left ({issue['direct_matches']} total, {issue['mapped_away']} mapped)")

if __name__ == "__main__":
    print("=== Comprehensive Mapping Issues Check ===\\n")
    
    test_sub_match_display()
    test_player_stats_display() 
    find_unmapped_first_names()
    
    print(f"\\n=== Check Complete ===")