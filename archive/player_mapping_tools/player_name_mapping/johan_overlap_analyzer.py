#!/usr/bin/env python3
"""
Johan Overlap Analyzer
Check for temporal overlaps between the remaining Johan matches and specific Johan players.

Created: 2025-09-22
"""
import sqlite3
from datetime import datetime
from collections import defaultdict

def get_remaining_johan_matches_by_context():
    """Get remaining Johan matches grouped by context"""
    with sqlite3.connect("../goldenstat.db") as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
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
        ORDER BY m.match_date
        """
        
        cursor.execute(query)
        matches = cursor.fetchall()
        
        # Group by context
        by_context = defaultdict(list)
        for match in matches:
            club = match['team_name'].split('(')[0].strip()
            context = f"{club} ({match['division']}) {match['season']}"
            by_context[context].append(match)
        
        return by_context

def get_johan_player_timeline(player_name):
    """Get activity timeline for a specific Johan player"""
    with sqlite3.connect("../goldenstat.db") as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        query = """
        SELECT 
            m.match_date,
            m.season,
            m.division,
            CASE WHEN smp.team_number = 1 THEN t1.name ELSE t2.name END as team_name
            
        FROM players p
        JOIN sub_match_participants smp ON p.id = smp.player_id
        JOIN sub_matches sm ON smp.sub_match_id = sm.id
        JOIN matches m ON sm.match_id = m.id
        JOIN teams t1 ON m.team1_id = t1.id
        JOIN teams t2 ON m.team2_id = t2.id
        
        WHERE p.name = ?
        ORDER BY m.match_date
        """
        
        cursor.execute(query, (player_name,))
        return cursor.fetchall()

def extract_club_name(team_name):
    """Extract club name from team name"""
    return team_name.split('(')[0].strip()

def check_temporal_overlap(johan_matches, player_timeline, context_info):
    """Check if there's temporal overlap between Johan matches and a specific player"""
    johan_dates = [m['match_date'] for m in johan_matches]
    johan_start = min(johan_dates)
    johan_end = max(johan_dates)
    
    # Get player matches in same context
    context_club, context_division, context_season = context_info
    
    overlapping_matches = []
    for match in player_timeline:
        match_club = extract_club_name(match['team_name'])
        
        # Check if it's the same club and season
        if (match_club.lower() == context_club.lower() and 
            match['season'] == context_season):
            overlapping_matches.append(match)
    
    if not overlapping_matches:
        return None, "No matches in same context"
    
    player_dates = [m['match_date'] for m in overlapping_matches]
    player_start = min(player_dates)
    player_end = max(player_dates)
    
    # Check temporal overlap
    overlap_start = max(johan_start, player_start)
    overlap_end = min(johan_end, player_end)
    
    if overlap_start <= overlap_end:
        return overlapping_matches, f"OVERLAP: {overlap_start[:10]} to {overlap_end[:10]}"
    else:
        gap_days = (datetime.fromisoformat(overlap_start.replace(' ', 'T')) - 
                   datetime.fromisoformat(overlap_end.replace(' ', 'T'))).days
        return overlapping_matches, f"GAP: {gap_days} days between {overlap_end[:10]} and {overlap_start[:10]}"

def analyze_overlaps():
    """Main analysis function"""
    print("=== Johan Overlap Analysis ===\n")
    
    remaining_contexts = get_remaining_johan_matches_by_context()
    
    # Focus on the big clusters
    big_clusters = [
        ("Rockhangers", "2FA", "2024/2025"),
        ("Tyresö", "SL4", "2024/2025"),
        ("Oasen", "3FD", "2023/2024"),
        ("Nacka Wermdö", "3FB", "2023/2024")
    ]
    
    # Get candidate Johan players who were active in those periods
    johan_candidates = [
        "Johan Rosander", "Johan Engström", "Johan Brink", "Johan tidblad",
        "Johan Lööf", "Johan Jakobsson", "Johan Karlsson", "Johan Ramberg",
        "Johan Jonsson", "Johan Hansson", "Johan Legerstam"
    ]
    
    for club, division, season in big_clusters:
        context_key = f"{club} ({division}) {season}"
        if context_key in remaining_contexts:
            johan_matches = remaining_contexts[context_key]
            
            print(f"=== {context_key} ({len(johan_matches)} matches) ===")
            print(f"Johan match period: {min(m['match_date'] for m in johan_matches)[:10]} to {max(m['match_date'] for m in johan_matches)[:10]}")
            print()
            
            # Check each candidate
            for candidate in johan_candidates:
                timeline = get_johan_player_timeline(candidate)
                if timeline:
                    overlaps, result = check_temporal_overlap(
                        johan_matches, timeline, (club, division, season)
                    )
                    
                    if overlaps:
                        print(f"  {candidate}: {result}")
                        print(f"    {len(overlaps)} matches in {club} {season}")
                        if overlaps:
                            sample_dates = sorted(set(m['match_date'][:10] for m in overlaps))[:3]
                            print(f"    Sample dates: {', '.join(sample_dates)}")
                        print()
            
            print("-" * 50)
            print()

if __name__ == "__main__":
    analyze_overlaps()