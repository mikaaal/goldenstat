#!/usr/bin/env python3
"""
Universal First Name Mapper
A generalized script that can map any first-name-only player to specific players
and create contextual players for remaining matches.

Created: 2025-09-22
"""
import sqlite3
import sys
from collections import defaultdict
from datetime import datetime

class UniversalFirstNameMapper:
    def __init__(self, db_path="../goldenstat.db"):
        self.db_path = db_path
    
    def extract_club_name(self, team_name):
        """Extract club name from 'Club (Division)' format"""
        if '(' in team_name:
            return team_name.split('(')[0].strip()
        return team_name.strip()
    
    def get_first_name_only_players(self, min_matches=10):
        """Find all players with only first names who have enough matches to be worth mapping"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            query = """
            SELECT DISTINCT p.id, p.name, COUNT(DISTINCT smp.sub_match_id) as match_count
            FROM players p
            JOIN sub_match_participants smp ON p.id = smp.player_id
            WHERE LENGTH(p.name) <= 15  -- Reasonable first name length
                AND p.name NOT LIKE '% %'  -- No spaces (no last name)
                AND p.name NOT LIKE '%(%'  -- No parentheses
                AND p.name NOT LIKE '%.%'  -- No abbreviations like "P."
                AND LENGTH(p.name) >= 3    -- At least 3 characters
                AND p.name NOT IN ('Peter', 'Johan')  -- Already handled
            GROUP BY p.id, p.name
            HAVING match_count >= ?
            ORDER BY match_count DESC, p.name
            """
            
            cursor.execute(query, (min_matches,))
            return cursor.fetchall()
    
    def find_potential_full_name_matches(self, first_name):
        """Find players with full names that start with the given first name"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            query = """
            SELECT DISTINCT p.id, p.name, COUNT(DISTINCT smp.sub_match_id) as match_count
            FROM players p
            JOIN sub_match_participants smp ON p.id = smp.player_id
            WHERE p.name LIKE ? || ' %'  -- Starts with first name + space
                AND LENGTH(p.name) > LENGTH(?)  -- Longer than just first name
            GROUP BY p.id, p.name
            HAVING match_count >= 1
            ORDER BY match_count DESC
            """
            
            cursor.execute(query, (first_name, first_name))
            return cursor.fetchall()
    
    def get_player_context_timeline(self, player_id):
        """Get detailed timeline and context for a specific player"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            query = """
            SELECT 
                p.id as player_id,
                p.name as player_name,
                t.name as team_name,
                m.division,
                m.season,
                MIN(m.match_date) as first_match,
                MAX(m.match_date) as last_match,
                COUNT(DISTINCT sm.id) as match_count
                
            FROM players p
            JOIN sub_match_participants smp ON p.id = smp.player_id
            JOIN sub_matches sm ON smp.sub_match_id = sm.id
            JOIN matches m ON sm.match_id = m.id
            JOIN teams t ON (
                CASE WHEN smp.team_number = 1 THEN m.team1_id ELSE m.team2_id END
            ) = t.id
            
            WHERE p.id = ?
            GROUP BY p.id, p.name, t.name, m.division, m.season
            ORDER BY m.season, m.division
            """
            
            cursor.execute(query, (player_id,))
            return cursor.fetchall()
    
    def get_first_name_matches_with_context(self, first_name_player_id):
        """Get all matches for a first-name-only player with context"""
        with sqlite3.connect(self.db_path) as conn:
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
            
            WHERE p.id = ?
            ORDER BY m.match_date
            """
            
            cursor.execute(query, (first_name_player_id,))
            return cursor.fetchall()
    
    def find_best_temporal_match(self, first_name_match, potential_full_names_timelines):
        """Find best temporal match using the proven algorithm"""
        match_club = self.extract_club_name(first_name_match['team_name'])
        match_division = first_name_match['division']
        match_season = first_name_match['season']
        match_date = first_name_match['match_date']
        
        candidates = []
        
        # Filter to same club/division/season first
        relevant_timelines = [
            timeline for timeline in potential_full_names_timelines
            if (self.extract_club_name(timeline['team_name']).lower() == match_club.lower() and
                timeline['division'] == match_division and
                timeline['season'] == match_season)
        ]
        
        if not relevant_timelines:
            # Fallback: same club and season, any division
            relevant_timelines = [
                timeline for timeline in potential_full_names_timelines
                if (self.extract_club_name(timeline['team_name']).lower() == match_club.lower() and
                    timeline['season'] == match_season)
            ]
        
        for timeline in relevant_timelines:
            # Calculate temporal proximity score
            first_date = timeline['first_match']
            last_date = timeline['last_match']
            
            # Check if match falls within this player's active period
            if first_date <= match_date <= last_date:
                temporal_score = 100  # Perfect temporal match
            else:
                # Calculate distance to closest boundary
                try:
                    date_obj = datetime.fromisoformat(match_date.replace(' ', 'T'))
                    first_obj = datetime.fromisoformat(first_date.replace(' ', 'T'))
                    last_obj = datetime.fromisoformat(last_date.replace(' ', 'T'))
                    
                    if date_obj < first_obj:
                        days_diff = (first_obj - date_obj).days
                    elif date_obj > last_obj:
                        days_diff = (date_obj - last_obj).days
                    else:
                        days_diff = 0
                    
                    # Score decreases with temporal distance
                    temporal_score = max(0, 100 - days_diff)
                except:
                    temporal_score = 0
            
            # Context matching score
            context_score = 0
            if timeline['division'] == match_division:
                context_score += 30
            if timeline['season'] == match_season:
                context_score += 20
            
            total_score = temporal_score + context_score
            
            candidates.append({
                'player_id': timeline['player_id'],
                'player_name': timeline['player_name'],
                'timeline': timeline,
                'temporal_score': temporal_score,
                'context_score': context_score,
                'total_score': total_score,
                'reasoning': f"Temporal: {temporal_score}, Context: {context_score}"
            })
        
        # Sort by total score, then by temporal score
        candidates.sort(key=lambda x: (x['total_score'], x['temporal_score']), reverse=True)
        
        return candidates[0] if candidates else None
    
    def analyze_first_name_player(self, first_name_player, confidence_threshold=80):
        """Analyze a specific first-name player for potential mappings"""
        first_name = first_name_player['name']
        player_id = first_name_player['id']
        
        print(f"\\n=== Analyzing '{first_name}' (ID: {player_id}, {first_name_player['match_count']} matches) ===")
        
        # Find potential full-name matches
        potential_matches = self.find_potential_full_name_matches(first_name)
        
        if not potential_matches:
            print(f"  No potential full-name matches found for '{first_name}'")
            return []
        
        print(f"  Found {len(potential_matches)} potential full-name matches")
        
        # Get timelines for all potential matches
        all_timelines = []
        for potential_match in potential_matches:
            timelines = self.get_player_context_timeline(potential_match['id'])
            all_timelines.extend(timelines)
        
        # Get all first-name matches
        first_name_matches = self.get_first_name_matches_with_context(player_id)
        
        print(f"  Analyzing {len(first_name_matches)} '{first_name}' matches...")
        
        mappings = []
        
        # Analyze each first-name match
        for fn_match in first_name_matches:
            best_match = self.find_best_temporal_match(fn_match, all_timelines)
            
            if best_match and best_match['total_score'] >= confidence_threshold:
                mappings.append({
                    'sub_match_id': fn_match['sub_match_id'],
                    'first_name_player_id': player_id,
                    'first_name': first_name,
                    'match_date': fn_match['match_date'],
                    'match_context': f"{fn_match['team_name']} ({fn_match['division']}) {fn_match['season']}",
                    'target_player_id': best_match['player_id'],
                    'target_player_name': best_match['player_name'],
                    'confidence': best_match['total_score'],
                    'temporal_score': best_match['temporal_score'],
                    'reasoning': best_match['reasoning']
                })
        
        # Summarize results
        by_target = defaultdict(list)
        for mapping in mappings:
            by_target[mapping['target_player_name']].append(mapping)
        
        print(f"  Successfully mapped: {len(mappings)}/{len(first_name_matches)} matches")
        
        if by_target:
            print(f"  Mappings by target:")
            for target_name, target_mappings in sorted(by_target.items()):
                avg_conf = sum(m['confidence'] for m in target_mappings) / len(target_mappings)
                print(f"    {target_name}: {len(target_mappings)} matches (avg conf: {avg_conf:.1f})")
        
        return mappings
    
    def get_remaining_matches(self, first_name_player_id):
        """Get matches that weren't mapped away for a first-name player"""
        with sqlite3.connect(self.db_path) as conn:
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
            
            WHERE p.id = ?
            AND smp.sub_match_id NOT IN (
                SELECT smpm.sub_match_id 
                FROM sub_match_player_mappings smpm 
                WHERE smpm.original_player_id = ?
            )
            ORDER BY m.match_date
            """
            
            cursor.execute(query, (first_name_player_id, first_name_player_id))
            return cursor.fetchall()
    
    def create_contextual_mappings(self, first_name_player_id, first_name, min_context_matches=5):
        """Create contextual mappings for remaining matches"""
        remaining_matches = self.get_remaining_matches(first_name_player_id)
        
        if not remaining_matches:
            return []
        
        print(f"\\n  Creating contextual mappings for {len(remaining_matches)} remaining {first_name} matches")
        
        # Group by context
        by_context = defaultdict(list)
        for match in remaining_matches:
            club = self.extract_club_name(match['team_name'])
            by_context[club].append(match)
        
        contextual_mappings = []
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            for context, matches in by_context.items():
                if len(matches) >= min_context_matches:
                    contextual_name = f"{first_name} ({context})"
                    
                    # Check if player already exists
                    cursor.execute("SELECT id FROM players WHERE name = ?", (contextual_name,))
                    result = cursor.fetchone()
                    
                    if result:
                        player_id = result[0]
                    else:
                        # Create new contextual player
                        cursor.execute("INSERT INTO players (name) VALUES (?)", (contextual_name,))
                        player_id = cursor.lastrowid
                        print(f"    Created: {contextual_name} (ID: {player_id})")
                    
                    # Create mappings for all matches in this context
                    for match in matches:
                        contextual_mappings.append({
                            'sub_match_id': match['sub_match_id'],
                            'first_name_player_id': first_name_player_id,
                            'first_name': first_name,
                            'match_date': match['match_date'],
                            'match_context': f"{match['team_name']} ({match['division']}) {match['season']}",
                            'target_player_id': player_id,
                            'target_player_name': contextual_name,
                            'confidence': 95,
                            'temporal_score': 95,
                            'reasoning': f"Contextual mapping based on club consistency ({context})"
                        })
            
            conn.commit()
        
        return contextual_mappings
    
    def apply_mappings_to_database(self, all_mappings):
        """Apply all mappings to the sub_match_player_mappings table"""
        if not all_mappings:
            return
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            for mapping in all_mappings:
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
                    mapping['first_name_player_id'],
                    mapping['target_player_id'],
                    mapping['target_player_name'],
                    mapping['match_context'],
                    min(100, mapping['confidence']),
                    mapping['reasoning'],
                    f"Universal mapping: {mapping['temporal_score']}/100"
                ))
            
            conn.commit()
            print(f"\\n✓ Applied {len(all_mappings)} mappings to database")
    
    def process_first_name(self, first_name_player):
        """Process a single first-name player with both temporal and contextual mapping"""
        first_name = first_name_player['name']
        player_id = first_name_player['id']
        
        # Step 1: Find temporal mappings to existing full-name players
        temporal_mappings = self.analyze_first_name_player(first_name_player)
        
        # Step 2: Create contextual mappings for remaining matches
        contextual_mappings = self.create_contextual_mappings(player_id, first_name)
        
        # Combine all mappings
        all_mappings = temporal_mappings + contextual_mappings
        
        print(f"  Total mappings for {first_name}: {len(all_mappings)} ({len(temporal_mappings)} temporal + {len(contextual_mappings)} contextual)")
        
        return all_mappings

def main():
    """Main function to process multiple first names"""
    print("=== Universal First Name Mapper ===\\n")
    
    # Check command line arguments
    if len(sys.argv) > 1:
        # Specific first names provided
        target_names = sys.argv[1:]
        print(f"Processing specific names: {', '.join(target_names)}")
    else:
        # Auto-detect first-name-only players
        mapper = UniversalFirstNameMapper()
        first_name_players = mapper.get_first_name_only_players(min_matches=20)
        
        print(f"Found {len(first_name_players)} first-name-only players with 20+ matches:")
        for i, player in enumerate(first_name_players[:10]):
            print(f"  {i+1}. {player['name']}: {player['match_count']} matches")
        
        if len(first_name_players) > 10:
            print(f"  ... and {len(first_name_players) - 10} more")
        
        # Process top candidates
        target_names = [p['name'] for p in first_name_players[:5]]
        print(f"\\nProcessing top 5: {', '.join(target_names)}")
    
    # Process each target name
    mapper = UniversalFirstNameMapper()
    all_mappings = []
    
    for target_name in target_names:
        # Get player info
        with sqlite3.connect(mapper.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT p.id, p.name, COUNT(DISTINCT smp.sub_match_id) as match_count
                FROM players p
                JOIN sub_match_participants smp ON p.id = smp.player_id
                WHERE p.name = ?
                GROUP BY p.id, p.name
            """, (target_name,))
            
            player_info = cursor.fetchone()
            
            if not player_info:
                print(f"\\nPlayer '{target_name}' not found, skipping...")
                continue
            
            player_dict = {
                'id': player_info['id'],
                'name': player_info['name'],
                'match_count': player_info['match_count']
            }
            
            # Process this player
            mappings = mapper.process_first_name(player_dict)
            all_mappings.extend(mappings)
    
    # Apply all mappings to database
    if all_mappings:
        mapper.apply_mappings_to_database(all_mappings)
        
        # Final summary
        by_original = defaultdict(list)
        for mapping in all_mappings:
            by_original[mapping['first_name']].append(mapping)
        
        print(f"\\n=== Final Summary ===")
        print(f"Processed {len(by_original)} first names with {len(all_mappings)} total mappings")
        
        for first_name, mappings in by_original.items():
            by_target = defaultdict(list)
            for mapping in mappings:
                by_target[mapping['target_player_name']].append(mapping)
            
            print(f"\\n{first_name}: {len(mappings)} mappings to {len(by_target)} targets")
            for target_name, target_mappings in sorted(by_target.items(), key=lambda x: len(x[1]), reverse=True):
                print(f"  {target_name}: {len(target_mappings)} matches")
    
    print(f"\\n✓ Universal mapping completed!")

if __name__ == "__main__":
    main()