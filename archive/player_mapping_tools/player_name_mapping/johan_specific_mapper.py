#!/usr/bin/env python3
"""
Johan Specific Mapper
Focus on just Johan to create sub-match mappings like we did for Peter.

Created: 2025-09-22
"""
import sqlite3
import sys
sys.path.append('.')
from first_name_only_mapper import FirstNameOnlyMapper

def analyze_johan_only():
    """Analyze just Johan and create mappings"""
    print("=== Johan Specific Analysis ===\n")
    
    mapper = FirstNameOnlyMapper()
    
    # Get Johan's player record
    with sqlite3.connect("../goldenstat.db") as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("SELECT id, name FROM players WHERE name = 'Johan'")
        johan_player = cursor.fetchone()
        
        if not johan_player:
            print("Johan player not found!")
            return []
        
        johan_dict = {
            'id': johan_player['id'],
            'name': johan_player['name'],
            'match_count': 217  # We know this from the analysis
        }
    
    # Run the analysis specifically for Johan
    mappings = mapper.analyze_first_name_player(johan_dict)
    
    return mappings

def create_johan_submatch_mappings(mappings):
    """Create sub-match mappings for Johan like we did for Peter"""
    print(f"\n=== Creating Sub-Match Mappings for Johan ===")
    print(f"Applying {len(mappings)} confident mappings")
    
    with sqlite3.connect("../goldenstat.db") as conn:
        cursor = conn.cursor()
        
        # Apply the mappings to the sub_match_player_mappings table
        for mapping in mappings:
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
                mapping['sub_match_id'],
                mapping['first_name_player_id'],  # Johan's ID (750)
                mapping['target_player_id'],
                mapping['target_player_name'],
                mapping['match_context'],
                min(100, mapping['confidence']),  # Cap at 100
                mapping['reasoning'],
                f"Johan temporal mapping: {mapping['temporal_score']}/100"
            ))
        
        conn.commit()
        print(f"✓ Applied {len(mappings)} sub-match mappings for Johan")
        
        # Show summary
        cursor.execute("""
            SELECT correct_player_name, COUNT(*) as mapped_matches
            FROM sub_match_player_mappings 
            WHERE original_player_id = 750  -- Johan's ID
            GROUP BY correct_player_name 
            ORDER BY mapped_matches DESC
        """)
        
        results = cursor.fetchall()
        print("\nJohan mappings by target player:")
        for player_name, count in results:
            print(f"  {player_name}: {count} sub-matches")

if __name__ == "__main__":
    # Analyze Johan
    mappings = analyze_johan_only()
    
    if mappings:
        # Create the sub-match mappings
        create_johan_submatch_mappings(mappings)
        print(f"\n✓ Johan mapping system implemented!")
        print(f"Created {len(mappings)} sub-match mappings for Johan")
    else:
        print("No confident mappings found for Johan")