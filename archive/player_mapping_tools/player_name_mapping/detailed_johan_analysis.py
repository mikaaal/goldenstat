#!/usr/bin/env python3
"""
Detailed Johan Analysis
Look more carefully at the big clusters to find the right mappings.

Created: 2025-09-22
"""
import sqlite3
from collections import defaultdict

def extract_club_name(team_name):
    """Extract club name from 'Club (Division)' format"""
    if '(' in team_name:
        return team_name.split('(')[0].strip()
    return team_name.strip()

def find_johan_in_context(club, season, min_matches=5):
    """Find Johan candidates for a specific club/season context"""
    with sqlite3.connect("../goldenstat.db") as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Search more broadly - any Johan candidates who played for this club in this season
        # regardless of exact division
        query = """
        SELECT DISTINCT p.id, p.name, 
               COUNT(DISTINCT smp.sub_match_id) as match_count,
               MIN(m.match_date) as first_match,
               MAX(m.match_date) as last_match,
               GROUP_CONCAT(DISTINCT m.division) as divisions,
               GROUP_CONCAT(DISTINCT 
                   CASE WHEN smp.team_number = 1 THEN t1.name ELSE t2.name END
               ) as teams
        FROM players p
        JOIN sub_match_participants smp ON p.id = smp.player_id
        JOIN sub_matches sm ON smp.sub_match_id = sm.id
        JOIN matches m ON sm.match_id = m.id
        JOIN teams t1 ON m.team1_id = t1.id
        JOIN teams t2 ON m.team2_id = t2.id
        
        WHERE p.name LIKE 'Johan%'  -- Broader search including case variations
        AND m.season = ?
        AND (
            (smp.team_number = 1 AND t1.name LIKE ? || '%') OR
            (smp.team_number = 2 AND t2.name LIKE ? || '%')
        )
        
        GROUP BY p.id, p.name
        HAVING match_count >= ?
        ORDER BY match_count DESC
        """
        
        cursor.execute(query, (season, club, club, min_matches))
        return cursor.fetchall()

def analyze_big_clusters():
    """Analyze the biggest clusters of remaining Johan matches"""
    print("=== Detailed Analysis of Big Johan Clusters ===\n")
    
    # The big clusters we identified
    clusters = [
        ("Rockhangers", "2024/2025", 36),
        ("Tyresö", "2024/2025", 35), 
        ("Oasen", "2023/2024", 34),
        ("Nacka Wermdö", "2023/2024", 28)
    ]
    
    for club, season, match_count in clusters:
        print(f"=== {club} {season} ({match_count} Johan matches) ===")
        
        # Find Johan candidates for this context
        candidates = find_johan_in_context(club, season, min_matches=1)
        
        if candidates:
            print(f"Found {len(candidates)} Johan candidates:")
            for candidate in candidates:
                print(f"  {candidate['name']}: {candidate['match_count']} matches")
                print(f"    {candidate['first_match'][:10]} to {candidate['last_match'][:10]}")
                print(f"    Divisions: {candidate['divisions']}")
                print(f"    Teams: {candidate['teams'][:100]}...")
                print()
        else:
            print("No Johan candidates found - let's check for case variations...")
            
            # Check for any players with names containing 'johan' (case insensitive)
            with sqlite3.connect("../goldenstat.db") as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                cursor.execute("""
                SELECT DISTINCT p.name
                FROM players p
                JOIN sub_match_participants smp ON p.id = smp.player_id
                JOIN sub_matches sm ON smp.sub_match_id = sm.id
                JOIN matches m ON sm.match_id = m.id
                JOIN teams t1 ON m.team1_id = t1.id
                JOIN teams t2 ON m.team2_id = t2.id
                
                WHERE LOWER(p.name) LIKE '%johan%'
                AND m.season = ?
                AND (
                    (smp.team_number = 1 AND t1.name LIKE ? || '%') OR
                    (smp.team_number = 2 AND t2.name LIKE ? || '%')
                )
                
                ORDER BY p.name
                """, (season, club, club))
                
                variations = cursor.fetchall()
                if variations:
                    print("Found name variations:")
                    for var in variations:
                        print(f"  {var['name']}")
                else:
                    print("No name variations found either")
        
        print()

def check_johan_activity_timelines():
    """Check if existing Johan players have activity that overlaps with the big clusters"""
    print("=== Checking Johan Activity Timelines ===\n")
    
    # Get activity timelines for top Johan players
    with sqlite3.connect("../goldenstat.db") as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Get top Johan players and their activity periods
        cursor.execute("""
        SELECT p.id, p.name, 
               COUNT(DISTINCT smp.sub_match_id) as total_matches,
               MIN(m.match_date) as first_match,
               MAX(m.match_date) as last_match,
               COUNT(DISTINCT m.season) as seasons,
               GROUP_CONCAT(DISTINCT m.season) as season_list
        FROM players p
        JOIN sub_match_participants smp ON p.id = smp.player_id
        JOIN sub_matches sm ON smp.sub_match_id = sm.id
        JOIN matches m ON sm.match_id = m.id
        
        WHERE p.name LIKE 'Johan %'
        
        GROUP BY p.id, p.name
        HAVING total_matches >= 20
        ORDER BY total_matches DESC
        LIMIT 15
        """)
        
        johan_players = cursor.fetchall()
        
        print("Top Johan players and their activity periods:")
        for player in johan_players:
            print(f"{player['name']}: {player['total_matches']} matches")
            print(f"  Active: {player['first_match'][:10]} to {player['last_match'][:10]}")
            print(f"  Seasons: {player['season_list']}")
            print()

if __name__ == "__main__":
    analyze_big_clusters()
    check_johan_activity_timelines()