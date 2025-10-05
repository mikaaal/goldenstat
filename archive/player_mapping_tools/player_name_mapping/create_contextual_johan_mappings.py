#!/usr/bin/env python3
"""
Create Contextual Johan Mappings
Create mappings for remaining Johan matches to context-specific Johan players
like "Johan (Rockhangers)", "Johan (Tyresö)" etc.

Created: 2025-09-22
"""
import sqlite3
from collections import defaultdict

def extract_club_name(team_name):
    """Extract club name from 'Club (Division)' format"""
    if '(' in team_name:
        return team_name.split('(')[0].strip()
    return team_name.strip()

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
        ORDER BY m.match_date
        """
        
        cursor.execute(query)
        return cursor.fetchall()

def group_matches_by_context(matches):
    """Group matches by club context"""
    by_context = defaultdict(list)
    
    for match in matches:
        club = extract_club_name(match['team_name'])
        context = f"{club}"  # Just use club name for simplicity
        by_context[context].append(match)
    
    return by_context

def create_contextual_players(context_groups):
    """Create contextual Johan players and return their IDs"""
    contextual_players = {}
    
    with sqlite3.connect("../goldenstat.db") as conn:
        cursor = conn.cursor()
        
        for context, matches in context_groups.items():
            if len(matches) >= 3:  # Only create for contexts with multiple matches
                contextual_name = f"Johan ({context})"
                
                # Check if player already exists
                cursor.execute("SELECT id FROM players WHERE name = ?", (contextual_name,))
                result = cursor.fetchone()
                
                if result:
                    player_id = result[0]
                    print(f"Using existing player: {contextual_name} (ID: {player_id})")
                else:
                    # Create new contextual player
                    cursor.execute("INSERT INTO players (name) VALUES (?)", (contextual_name,))
                    player_id = cursor.lastrowid
                    print(f"Created new player: {contextual_name} (ID: {player_id})")
                
                contextual_players[context] = {
                    'id': player_id,
                    'name': contextual_name,
                    'matches': matches
                }
        
        conn.commit()
    
    return contextual_players

def create_sub_match_mappings(contextual_players):
    """Create sub-match mappings for contextual Johan players"""
    total_mappings = 0
    
    with sqlite3.connect("../goldenstat.db") as conn:
        cursor = conn.cursor()
        
        for context, player_info in contextual_players.items():
            matches = player_info['matches']
            target_player_id = player_info['id']
            target_player_name = player_info['name']
            
            print(f"\\nCreating mappings for {target_player_name}: {len(matches)} matches")
            
            for match in matches:
                # Create sub-match mapping
                cursor.execute("""
                    INSERT OR REPLACE INTO sub_match_player_mappings (
                        sub_match_id,
                        original_player_id,
                        correct_player_id, 
                        correct_player_name,
                        match_context,
                        confidence,
                        mapping_reason,
                        notes
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    match['sub_match_id'],
                    750,  # Johan's original ID
                    target_player_id,
                    target_player_name,
                    f"{match['team_name']} ({match['division']}) {match['season']}",
                    95,  # High confidence for contextual mapping
                    f"Contextual mapping based on club consistency",
                    f"Mapped to {context} context - {match['match_date'][:10]}"
                ))
                
                total_mappings += 1
        
        conn.commit()
        print(f"\\n✓ Created {total_mappings} contextual mappings")

def analyze_and_create_contextual_mappings():
    """Main function to analyze and create contextual mappings"""
    print("=== Creating Contextual Johan Mappings ===\\n")
    
    # Get remaining matches
    remaining_matches = get_remaining_johan_matches()
    print(f"Found {len(remaining_matches)} remaining Johan matches")
    
    # Group by context
    context_groups = group_matches_by_context(remaining_matches)
    
    print(f"\\nGrouped into {len(context_groups)} contexts:")
    for context, matches in sorted(context_groups.items(), key=lambda x: len(x[1]), reverse=True):
        if len(matches) >= 3:
            dates = [m['match_date'][:10] for m in matches]
            date_range = f"{min(dates)} to {max(dates)}"
            seasons = sorted(set(m['season'] for m in matches))
            print(f"  {context}: {len(matches)} matches [{date_range}] Seasons: {', '.join(seasons)}")
    
    # Create contextual players
    print(f"\\n=== Creating Contextual Players ===")
    contextual_players = create_contextual_players(context_groups)
    
    # Create mappings
    print(f"\\n=== Creating Sub-Match Mappings ===")
    create_sub_match_mappings(contextual_players)
    
    # Show final summary
    with sqlite3.connect("../goldenstat.db") as conn:
        cursor = conn.cursor()
        
        # Count total mappings for Johan
        cursor.execute("""
            SELECT COUNT(*) 
            FROM sub_match_player_mappings 
            WHERE original_player_id = 750
        """)
        total_johan_mappings = cursor.fetchone()[0]
        
        # Show breakdown by target
        cursor.execute("""
            SELECT correct_player_name, COUNT(*) as mapped_matches
            FROM sub_match_player_mappings 
            WHERE original_player_id = 750
            GROUP BY correct_player_name 
            ORDER BY mapped_matches DESC
        """)
        
        results = cursor.fetchall()
        print(f"\\n=== Final Johan Mapping Summary ===")
        print(f"Total Johan sub-matches mapped: {total_johan_mappings}")
        print(f"\\nMappings by target player:")
        for player_name, count in results:
            print(f"  {player_name}: {count} sub-matches")

def verify_johan_counts():
    """Verify that Johan now shows fewer matches"""
    print(f"\\n=== Verification ===")
    
    with sqlite3.connect("../goldenstat.db") as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Count remaining Johan matches
        cursor.execute("""
            SELECT COUNT(DISTINCT smp.sub_match_id) as remaining_matches
            FROM players p
            JOIN sub_match_participants smp ON p.id = smp.player_id
            WHERE p.name = 'Johan'
            AND smp.sub_match_id NOT IN (
                SELECT smpm.sub_match_id 
                FROM sub_match_player_mappings smpm 
                WHERE smpm.original_player_id = 750
            )
        """)
        
        result = cursor.fetchone()
        remaining = result['remaining_matches'] if result else 0
        
        print(f"Johan should now show {remaining} matches in the app")

if __name__ == "__main__":
    analyze_and_create_contextual_mappings()
    verify_johan_counts()