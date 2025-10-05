#!/usr/bin/env python3
"""
Implement Sub-Match Level Mappings
Instead of mapping entire player IDs, we map specific sub_matches to correct players.
This prevents the issue where all specific Peters get ALL Peter matches.

Created: 2025-09-22
"""
import sqlite3
import sys
sys.path.append('.')
from temporal_aware_splitter import TemporalAwareSplitter

def create_submatch_mapping_table():
    """Create the sub-match level mapping table"""
    with sqlite3.connect("../goldenstat.db") as conn:
        cursor = conn.cursor()
        
        # Drop the problematic player-level mapping table
        cursor.execute("DROP TABLE IF EXISTS player_name_mappings;")
        
        # Create sub-match level mapping table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sub_match_player_mappings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                
                -- The specific sub_match that needs remapping
                sub_match_id INTEGER NOT NULL,
                
                -- The original player ID in that sub_match (should be "Peter" = 386)
                original_player_id INTEGER NOT NULL,
                
                -- The correct player this sub_match should belong to
                correct_player_id INTEGER NOT NULL,
                correct_player_name TEXT NOT NULL,
                
                -- Context and confidence
                match_context TEXT,
                confidence INTEGER DEFAULT 80 CHECK (confidence BETWEEN 1 AND 100),
                mapping_reason TEXT,
                
                -- Metadata
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                notes TEXT,
                
                -- Constraints
                FOREIGN KEY (sub_match_id) REFERENCES sub_matches(id),
                FOREIGN KEY (original_player_id) REFERENCES players(id),
                FOREIGN KEY (correct_player_id) REFERENCES players(id),
                UNIQUE(sub_match_id, original_player_id),
                CHECK(original_player_id != correct_player_id)
            );
        """)
        
        # Create indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_sub_match_mappings_sub_match ON sub_match_player_mappings(sub_match_id);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_sub_match_mappings_original ON sub_match_player_mappings(original_player_id);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_sub_match_mappings_correct ON sub_match_player_mappings(correct_player_id);")
        
        conn.commit()
        print("✓ Created sub_match_player_mappings table")

def apply_peter_temporal_mappings():
    """Use our temporal analysis to create correct sub-match mappings"""
    print("\\n=== Applying Peter Temporal Mappings ===")
    
    # Use our temporal splitter to get the correct mappings
    splitter = TemporalAwareSplitter()
    mappings, conflicts = splitter.analyze_peter_temporal_splitting()
    
    print(f"Generated {len(mappings)} confident mappings from temporal analysis")
    
    # Apply the mappings to the database
    with sqlite3.connect("../goldenstat.db") as conn:
        cursor = conn.cursor()
        
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
                386,  # Peter's ID
                mapping['target_player_id'],
                mapping['target_player_name'],
                mapping['peter_context'],
                min(100, mapping['confidence']),  # Cap at 100
                mapping['reasoning'],
                f"Temporal mapping: {mapping['temporal_score']}/100"
            ))
        
        conn.commit()
        print(f"✓ Applied {len(mappings)} sub-match mappings to database")
        
        # Show summary
        cursor.execute("""
            SELECT correct_player_name, COUNT(*) as mapped_matches
            FROM sub_match_player_mappings 
            GROUP BY correct_player_name 
            ORDER BY mapped_matches DESC
        """)
        
        results = cursor.fetchall()
        print("\\nMappings by target player:")
        for player_name, count in results:
            print(f"  {player_name}: {count} sub-matches")

def update_app_logic():
    """Update the app's get_effective_player_ids function to use sub-match mappings"""
    
    new_function = '''
def get_effective_player_ids(cursor, player_name):
    """
    Get all player IDs that should be included for a given player name, 
    using sub-match level mappings instead of player-level mappings.
    """
    # First get the base player ID(s)
    cursor.execute("""
        SELECT id as player_id
        FROM players
        WHERE name = ?
    """, (player_name,))
    
    base_results = cursor.fetchall()
    if not base_results:
        return []
    
    player_ids = [row['player_id'] for row in base_results]
    
    # Check if this player is a target of any sub-match mappings
    cursor.execute("""
        SELECT DISTINCT correct_player_id
        FROM sub_match_player_mappings
        WHERE correct_player_name = ?
    """, (player_name,))
    
    mapping_targets = cursor.fetchall()
    for target in mapping_targets:
        if target['correct_player_id'] not in player_ids:
            player_ids.append(target['correct_player_id'])
    
    return player_ids
'''
    
    print("\\n=== App Logic Update Needed ===")
    print("The app logic needs to be updated to:")
    print("1. Use sub_match_player_mappings instead of player_name_mappings")
    print("2. When fetching throws/matches, apply the sub-match mappings")
    print("3. Replace sub_match_participants data with mapped players")
    print("\\nThis requires updating the database queries in app.py and database.py")
    print("to use JOINs with the sub_match_player_mappings table.")

if __name__ == "__main__":
    print("=== Implementing Sub-Match Level Mappings ===")
    
    # Step 1: Create the new table structure
    create_submatch_mapping_table()
    
    # Step 2: Apply the temporal mappings 
    apply_peter_temporal_mappings()
    
    # Step 3: Explain what needs to be updated in the app
    update_app_logic()
    
    print("\\n✓ Sub-match mapping system implemented!")
    print("⚠ App logic needs to be updated to use the new mapping system")