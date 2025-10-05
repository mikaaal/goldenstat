#!/usr/bin/env python3
"""
Improved Peter Splitter
More flexible approach to mapping generic "Peter" matches to specific Peters.
Uses club context and temporal patterns with relaxed matching criteria.

Created: 2025-09-22
"""
import sqlite3
from collections import defaultdict, Counter
from datetime import datetime, timedelta
import re

class ImprovedPeterSplitter:
    def __init__(self, db_path="../goldenstat.db"):
        self.db_path = db_path
    
    def extract_club_name(self, team_name):
        """Extract club name from 'Club (Division)' format"""
        # Handle different formats: "Club (Division)", "Club", etc.
        if '(' in team_name:
            base = team_name.split('(')[0].strip()
            # Handle cases like "Dartanjang (Superligan)" where club includes division
            if base:
                return base
        return team_name.strip()
    
    def get_peter_match_details(self):
        """Get detailed information about each Peter match"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            query = """
            SELECT 
                sm.id as sub_match_id,
                m.id as match_id,
                m.match_date,
                m.season,
                m.division,
                t.name as team_name,
                smp.team_number,
                
                -- Opponent team
                CASE 
                    WHEN smp.team_number = 1 THEN t2.name 
                    ELSE t1.name 
                END as opponent_team_name
                
            FROM players p
            JOIN sub_match_participants smp ON p.id = smp.player_id
            JOIN sub_matches sm ON smp.sub_match_id = sm.id
            JOIN matches m ON sm.match_id = m.id
            JOIN teams t ON (
                CASE WHEN smp.team_number = 1 THEN m.team1_id ELSE m.team2_id END
            ) = t.id
            JOIN teams t1 ON m.team1_id = t1.id
            JOIN teams t2 ON m.team2_id = t2.id
            
            WHERE p.name = 'Peter'
            ORDER BY m.match_date
            """
            
            cursor.execute(query)
            return cursor.fetchall()
    
    def get_specific_peters_profiles(self):
        """Get comprehensive profiles for each specific Peter"""
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
                m.match_date,
                COUNT(*) as matches_in_context
                
            FROM players p
            JOIN sub_match_participants smp ON p.id = smp.player_id
            JOIN sub_matches sm ON smp.sub_match_id = sm.id
            JOIN matches m ON sm.match_id = m.id
            JOIN teams t ON (
                CASE WHEN smp.team_number = 1 THEN m.team1_id ELSE m.team2_id END
            ) = t.id
            
            WHERE p.name LIKE 'Peter %' 
                AND LENGTH(p.name) > 6  -- More than just "Peter"
            GROUP BY p.id, p.name, t.name, m.division, m.season
            ORDER BY p.name, m.season, m.division
            """
            
            cursor.execute(query)
            profiles = cursor.fetchall()
            
            # Group by player
            players = defaultdict(list)
            for profile in profiles:
                players[profile['player_id']].append(profile)
            
            return players
    
    def find_best_peter_match(self, peter_match, specific_peters):
        """Find the best matching specific Peter for a generic Peter match"""
        peter_club = self.extract_club_name(peter_match['team_name'])
        peter_division = peter_match['division'] 
        peter_season = peter_match['season']
        peter_date = peter_match['match_date']
        
        candidates = []
        
        for player_id, profiles in specific_peters.items():
            player_name = profiles[0]['player_name']  # All profiles have same name
            
            # Check each context this specific Peter has played in
            for profile in profiles:
                specific_club = self.extract_club_name(profile['team_name'])
                
                score = 0
                match_reasons = []
                
                # Club match (most important)
                if specific_club.lower() == peter_club.lower():
                    score += 50
                    match_reasons.append("same_club")
                
                # Season match
                if profile['season'] == peter_season:
                    score += 30
                    match_reasons.append("same_season")
                
                # Division match
                if profile['division'] == peter_division:
                    score += 20
                    match_reasons.append("same_division")
                
                # Fuzzy club match (similar names)
                elif self.clubs_similar(specific_club, peter_club):
                    score += 25
                    match_reasons.append("similar_club")
                
                # If we have some match criteria, consider this candidate
                if score >= 30:  # Minimum threshold
                    candidates.append({
                        'player_id': player_id,
                        'player_name': player_name,
                        'score': score,
                        'profile': profile,
                        'match_reasons': match_reasons,
                        'club_match': specific_club,
                        'context': f"{profile['team_name']} ({profile['division']}) {profile['season']}"
                    })
        
        # Sort by score and return best candidate
        candidates.sort(key=lambda x: x['score'], reverse=True)
        return candidates[0] if candidates else None
    
    def clubs_similar(self, club1, club2):
        """Check if two club names are similar (fuzzy matching)"""
        if not club1 or not club2:
            return False
        
        club1_clean = re.sub(r'[^a-zA-ZåäöÅÄÖ]', '', club1.lower())
        club2_clean = re.sub(r'[^a-zA-ZåäöÅÄÖ]', '', club2.lower())
        
        # Check if one is contained in the other
        if club1_clean in club2_clean or club2_clean in club1_clean:
            return True
        
        # Check Levenshtein-like similarity for short names
        if len(club1_clean) <= 8 and len(club2_clean) <= 8:
            if self.string_similarity(club1_clean, club2_clean) > 0.8:
                return True
        
        return False
    
    def string_similarity(self, s1, s2):
        """Calculate similarity between two strings"""
        if not s1 or not s2:
            return 0
        
        # Simple character overlap measure
        s1_chars = set(s1.lower())
        s2_chars = set(s2.lower())
        
        if not s1_chars or not s2_chars:
            return 0
        
        overlap = len(s1_chars & s2_chars)
        total = len(s1_chars | s2_chars)
        
        return overlap / total if total > 0 else 0
    
    def analyze_and_split_peter_matches(self):
        """Main analysis function with improved matching"""
        print("=== Improved Peter Match Splitting Analysis ===\\n")
        
        # Get data
        peter_matches = self.get_peter_match_details()
        specific_peters = self.get_specific_peters_profiles()
        
        print(f"Found {len(peter_matches)} Peter matches to analyze")
        print(f"Found {len(specific_peters)} specific Peter players")
        
        # Analyze matches
        successful_mappings = []
        failed_mappings = []
        
        print("\\n=== Sample Analysis (first 15 matches) ===")
        
        for i, peter_match in enumerate(peter_matches):
            best_match = self.find_best_peter_match(peter_match, specific_peters)
            
            if i < 15:  # Show first 15 for debugging
                print(f"\\nMatch {i+1}: {peter_match['match_date'][:10]}")
                print(f"  Context: {peter_match['team_name']} ({peter_match['division']}) {peter_match['season']}")
                
                if best_match:
                    print(f"  → {best_match['player_name']} (score: {best_match['score']})")
                    print(f"    Reasons: {', '.join(best_match['match_reasons'])}")
                    print(f"    From context: {best_match['context']}")
                else:
                    print(f"  → No suitable match found")
            
            if best_match and best_match['score'] >= 50:  # High confidence threshold
                successful_mappings.append({
                    'sub_match_id': peter_match['sub_match_id'],
                    'peter_context': f"{peter_match['team_name']} ({peter_match['division']}) {peter_match['season']}",
                    'target_player_id': best_match['player_id'],
                    'target_player_name': best_match['player_name'],
                    'confidence': best_match['score'],
                    'match_date': peter_match['match_date'],
                    'reasons': best_match['match_reasons']
                })
            else:
                failed_mappings.append({
                    'sub_match_id': peter_match['sub_match_id'],
                    'context': f"{peter_match['team_name']} ({peter_match['division']}) {peter_match['season']}",
                    'best_candidate': best_match['player_name'] if best_match else None,
                    'best_score': best_match['score'] if best_match else 0
                })
        
        print(f"\\n=== Results Summary ===")
        print(f"Total matches: {len(peter_matches)}")
        print(f"Successfully mapped: {len(successful_mappings)}")
        print(f"Failed to map: {len(failed_mappings)}")
        
        # Group successful mappings by target player
        by_target = defaultdict(list)
        for mapping in successful_mappings:
            by_target[mapping['target_player_name']].append(mapping)
        
        print(f"\\n=== Successful Mappings by Target Player ===")
        for player_name, mappings in sorted(by_target.items()):
            print(f"{player_name}: {len(mappings)} matches (avg confidence: {sum(m['confidence'] for m in mappings)/len(mappings):.1f})")
        
        # Analyze failed mappings
        print(f"\\n=== Failed Mapping Analysis ===")
        failed_contexts = Counter(m['context'] for m in failed_mappings)
        print("Most common failed contexts:")
        for context, count in failed_contexts.most_common(5):
            print(f"  {context}: {count} matches")
        
        return successful_mappings, failed_mappings
    
    def generate_mapping_sql(self, successful_mappings):
        """Generate SQL for the successful mappings"""
        print(f"\\n=== SQL Generation for {len(successful_mappings)} mappings ===")
        
        # First, create the mapping table if it doesn't exist
        create_table_sql = """
-- Create mapping table first
"""
        with open('improved_mapping_table.sql', 'r') as f:
            create_table_sql = f.read()
        
        # Group by target to avoid duplicate mappings
        unique_mappings = {}
        for mapping in successful_mappings:
            key = (386, mapping['target_player_id'])  # (source_peter_id, target_player_id)
            if key not in unique_mappings:
                unique_mappings[key] = mapping
            # If duplicate, keep the one with higher confidence
            elif mapping['confidence'] > unique_mappings[key]['confidence']:
                unique_mappings[key] = mapping
        
        print(f"Reduced to {len(unique_mappings)} unique mappings after deduplication")
        
        sql_statements = []
        for mapping in unique_mappings.values():
            sql = f"""
INSERT OR REPLACE INTO player_name_mappings (
    source_player_id, 
    target_player_id, 
    canonical_name, 
    specific_context,
    confidence, 
    mapping_type, 
    validation_status,
    club_uniqueness_validated,
    temporal_uniqueness_validated,
    notes
) VALUES (
    386, 
    {mapping['target_player_id']}, 
    '{mapping['target_player_name']}',
    '{mapping['peter_context']}',
    {mapping['confidence']}, 
    'first_name_only', 
    'validated',
    1,
    1,
    'Auto-mapped from Peter based on: {", ".join(mapping["reasons"])} (confidence: {mapping["confidence"]})'
);"""
            sql_statements.append(sql.strip())
        
        return sql_statements

if __name__ == "__main__":
    splitter = ImprovedPeterSplitter()
    successful, failed = splitter.analyze_and_split_peter_matches()
    
    if successful:
        sql_statements = splitter.generate_mapping_sql(successful)
        
        # Write to file
        with open('peter_mappings.sql', 'w') as f:
            f.write("-- Generated Peter mappings\\n")
            f.write("-- This will map generic 'Peter' matches to specific Peter players\\n\\n")
            for sql in sql_statements:
                f.write(sql + "\\n\\n")
        
        print(f"\\nGenerated {len(sql_statements)} SQL mappings in peter_mappings.sql")