#!/usr/bin/env python3
"""
Analyze Remaining Johan Matches
Look at the 133 matches that weren't mapped to see what patterns exist.

Created: 2025-09-22
"""
import sqlite3
from collections import defaultdict

def get_remaining_johan_matches():
    """Get the Johan matches that weren't mapped away"""
    with sqlite3.connect("../goldenstat.db") as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Get Johan matches excluding those that were mapped away
        query = """
        SELECT 
            sm.id as sub_match_id,
            m.match_date,
            m.season,
            m.division,
            CASE WHEN smp.team_number = 1 THEN t1.name ELSE t2.name END as team_name,
            smp.team_number,
            p.id as player_id,
            p.name as player_name
            
        FROM players p
        JOIN sub_match_participants smp ON p.id = smp.player_id
        JOIN sub_matches sm ON smp.sub_match_id = sm.id
        JOIN matches m ON sm.match_id = m.id
        JOIN teams t1 ON m.team1_id = t1.id
        JOIN teams t2 ON m.team2_id = t2.id
        
        WHERE p.name = 'Johan'
        AND smp.sub_match_id NOT IN (
            SELECT smpm.sub_match_id 
            FROM sub_match_player_mappings smpm 
            WHERE smpm.original_player_id = 750  -- Johan's ID
        )
        ORDER BY m.match_date DESC
        """
        
        cursor.execute(query)
        return cursor.fetchall()

def extract_club_name(team_name):
    """Extract club name from 'Club (Division)' format"""
    if '(' in team_name:
        return team_name.split('(')[0].strip()
    return team_name.strip()

def analyze_remaining_matches():
    """Analyze the remaining Johan matches"""
    print("=== Analyzing Remaining Johan Matches ===\n")
    
    matches = get_remaining_johan_matches()
    print(f"Found {len(matches)} remaining Johan matches\n")
    
    # Group by club/division/season
    by_context = defaultdict(list)
    
    for match in matches:
        club = extract_club_name(match['team_name'])
        context = f"{club} ({match['division']}) {match['season']}"
        by_context[context].append(match)
    
    # Sort by match count
    sorted_contexts = sorted(by_context.items(), key=lambda x: len(x[1]), reverse=True)
    
    print("=== Remaining matches by context ===")
    for context, context_matches in sorted_contexts:
        if len(context_matches) >= 3:  # Only show contexts with multiple matches
            dates = [m['match_date'][:10] for m in context_matches]
            date_range = f"{min(dates)} to {max(dates)}"
            print(f"{context}: {len(context_matches)} matches [{date_range}]")
    
    # Look for potential Johan candidates in those contexts
    print(f"\n=== Checking for potential Johan candidates ===")
    
    # Get all Johan candidates again
    with sqlite3.connect("../goldenstat.db") as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Find all Johan players with full names
        cursor.execute("""
            SELECT DISTINCT p.id, p.name, COUNT(DISTINCT smp.sub_match_id) as match_count
            FROM players p
            JOIN sub_match_participants smp ON p.id = smp.player_id
            WHERE p.name LIKE 'Johan %'
            GROUP BY p.id, p.name
            HAVING match_count >= 1
            ORDER BY match_count DESC
        """)
        
        johan_candidates = cursor.fetchall()
    
    print(f"Found {len(johan_candidates)} Johan candidates:")
    for candidate in johan_candidates[:20]:  # Show top 20
        print(f"  {candidate['name']}: {candidate['match_count']} matches")
    
    # Check specific high-volume contexts
    print(f"\n=== Detailed analysis of top contexts ===")
    
    for context, context_matches in sorted_contexts[:5]:  # Top 5 contexts
        if len(context_matches) >= 5:
            print(f"\n{context} ({len(context_matches)} matches):")
            
            # Extract club and check if any Johan candidates played for same club
            club = extract_club_name(context_matches[0]['team_name'])
            division = context_matches[0]['division']
            season = context_matches[0]['season']
            
            # Find Johan candidates who played for this club/division/season
            cursor.execute("""
                SELECT DISTINCT p.id, p.name, 
                       COUNT(DISTINCT smp.sub_match_id) as match_count,
                       MIN(m.match_date) as first_match,
                       MAX(m.match_date) as last_match
                FROM players p
                JOIN sub_match_participants smp ON p.id = smp.player_id
                JOIN sub_matches sm ON smp.sub_match_id = sm.id
                JOIN matches m ON sm.match_id = m.id
                JOIN teams t1 ON m.team1_id = t1.id
                JOIN teams t2 ON m.team2_id = t2.id
                
                WHERE p.name LIKE 'Johan %'
                AND m.division = ?
                AND m.season = ?
                AND (
                    (smp.team_number = 1 AND t1.name LIKE ? || '%') OR
                    (smp.team_number = 2 AND t2.name LIKE ? || '%')
                )
                
                GROUP BY p.id, p.name
                HAVING match_count >= 1
                ORDER BY match_count DESC
            """, (division, season, club, club))
            
            candidates_for_context = cursor.fetchall()
            
            if candidates_for_context:
                print(f"  Potential candidates from {club}:")
                for candidate in candidates_for_context:
                    print(f"    {candidate['name']}: {candidate['match_count']} matches ({candidate['first_match'][:10]} to {candidate['last_match'][:10]})")
            else:
                print(f"  No Johan candidates found for {club} {division} {season}")
            
            # Show sample dates from the remaining Johan matches
            sample_dates = sorted(set(m['match_date'][:10] for m in context_matches))[:5]
            print(f"  Sample 'Johan' match dates: {', '.join(sample_dates)}")

if __name__ == "__main__":
    analyze_remaining_matches()