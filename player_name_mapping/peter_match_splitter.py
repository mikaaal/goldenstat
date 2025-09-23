#!/usr/bin/env python3
"""
Peter Match Splitter
Analyzes the generic "Peter" player and attempts to split matches to specific Peters
based on club context and temporal analysis.

Created: 2025-09-22
"""
import sqlite3
from collections import defaultdict
from datetime import datetime
import json

class PeterMatchSplitter:
    def __init__(self, db_path="../goldenstat.db"):
        self.db_path = db_path
    
    def get_peter_matches_with_context(self):
        """Get all matches for generic 'Peter' with full context"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            query = """
            SELECT 
                p.id as peter_player_id,
                p.name as peter_name,
                sm.id as sub_match_id,
                m.id as match_id,
                m.match_date,
                m.season,
                m.division,
                t.name as team_name,
                smp.team_number,
                
                -- Get opponent team info
                CASE 
                    WHEN smp.team_number = 1 THEN t2.name 
                    ELSE t1.name 
                END as opponent_team_name,
                
                -- Get other players in same sub_match
                GROUP_CONCAT(
                    CASE 
                        WHEN smp2.player_id != p.id THEN p2.name 
                        ELSE NULL 
                    END
                ) as teammate_names
                
            FROM players p
            JOIN sub_match_participants smp ON p.id = smp.player_id
            JOIN sub_matches sm ON smp.sub_match_id = sm.id
            JOIN matches m ON sm.match_id = m.id
            JOIN teams t ON (
                CASE WHEN smp.team_number = 1 THEN m.team1_id ELSE m.team2_id END
            ) = t.id
            JOIN teams t1 ON m.team1_id = t1.id
            JOIN teams t2 ON m.team2_id = t2.id
            
            -- Join to get teammates
            LEFT JOIN sub_match_participants smp2 ON sm.id = smp2.sub_match_id
            LEFT JOIN players p2 ON smp2.player_id = p2.id
            
            WHERE p.name = 'Peter'
            GROUP BY sm.id, p.id, m.id, t.name, smp.team_number
            ORDER BY m.match_date, m.season, m.division
            """
            
            cursor.execute(query)
            return cursor.fetchall()
    
    def get_specific_peters_context(self):
        """Get context for all specific Peter players"""
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
                COUNT(DISTINCT sm.id) as match_count,
                
                -- Get common teammates
                GROUP_CONCAT(DISTINCT p2.name) as common_teammates
                
            FROM players p
            JOIN sub_match_participants smp ON p.id = smp.player_id
            JOIN sub_matches sm ON smp.sub_match_id = sm.id
            JOIN matches m ON sm.match_id = m.id
            JOIN teams t ON (
                CASE WHEN smp.team_number = 1 THEN m.team1_id ELSE m.team2_id END
            ) = t.id
            
            -- Get teammates
            LEFT JOIN sub_match_participants smp2 ON sm.id = smp2.sub_match_id AND smp2.player_id != p.id
            LEFT JOIN players p2 ON smp2.player_id = p2.id
            
            WHERE p.name LIKE 'Peter %' 
                AND p.name NOT LIKE '% Peter%'  -- Exclude names where Peter is not first name
            GROUP BY p.id, t.name, m.division, m.season
            ORDER BY p.name, m.season, m.division
            """
            
            cursor.execute(query)
            return cursor.fetchall()
    
    def extract_club_name(self, team_name):
        """Extract club name from 'Club (Division)' format"""
        if '(' in team_name:
            return team_name.split('(')[0].strip()
        return team_name.strip()
    
    def find_matching_peters(self, peter_match, specific_peters):
        """Find which specific Peters could have played this match"""
        peter_club = self.extract_club_name(peter_match['team_name'])
        peter_division = peter_match['division']
        peter_season = peter_match['season']
        peter_date = peter_match['match_date']
        peter_teammates = set((peter_match['teammate_names'] or '').split(','))
        peter_teammates.discard('')  # Remove empty strings
        
        candidates = []
        
        for specific_peter in specific_peters:
            specific_club = self.extract_club_name(specific_peter['team_name'])
            
            # Must match club, division, and season
            if (specific_club == peter_club and 
                specific_peter['division'] == peter_division and 
                specific_peter['season'] == peter_season):
                
                # Check if date is within the specific Peter's active period
                if (peter_date >= specific_peter['first_match'] and 
                    peter_date <= specific_peter['last_match']):
                    
                    # Check teammate overlap (if we have teammate data)
                    specific_teammates = set((specific_peter['common_teammates'] or '').split(','))
                    specific_teammates.discard('')
                    
                    teammate_overlap = len(peter_teammates & specific_teammates)
                    
                    candidates.append({
                        'player_id': specific_peter['player_id'],
                        'player_name': specific_peter['player_name'],
                        'club_match': specific_club == peter_club,
                        'division_match': specific_peter['division'] == peter_division,
                        'season_match': specific_peter['season'] == peter_season,
                        'date_in_range': True,
                        'teammate_overlap': teammate_overlap,
                        'confidence': self.calculate_confidence(
                            specific_club == peter_club,
                            specific_peter['division'] == peter_division,
                            specific_peter['season'] == peter_season,
                            teammate_overlap
                        )
                    })
        
        # Sort by confidence
        candidates.sort(key=lambda x: x['confidence'], reverse=True)
        return candidates
    
    def calculate_confidence(self, club_match, division_match, season_match, teammate_overlap):
        """Calculate confidence score for a match"""
        confidence = 0
        if club_match: confidence += 40
        if division_match: confidence += 30
        if season_match: confidence += 20
        confidence += min(teammate_overlap * 5, 10)  # Max 10 points for teammates
        return confidence
    
    def analyze_peter_splitting(self):
        """Main analysis function"""
        print("=== Analyzing Peter Match Splitting ===\\n")
        
        # Get all Peter matches
        peter_matches = self.get_peter_matches_with_context()
        print(f"Found {len(peter_matches)} sub-matches for generic 'Peter'")
        
        # Get all specific Peters
        specific_peters = self.get_specific_peters_context()
        specific_peter_names = set(sp['player_name'] for sp in specific_peters)
        print(f"Found {len(specific_peter_names)} specific Peter players:")
        for name in sorted(specific_peter_names):
            print(f"  - {name}")
        
        print("\\n=== Match Analysis ===")
        
        # Analyze each Peter match
        splitting_recommendations = []
        no_match_count = 0
        multiple_match_count = 0
        single_match_count = 0
        
        for i, peter_match in enumerate(peter_matches):
            if i < 10:  # Show details for first 10 matches
                print(f"\\nMatch {i+1}: {peter_match['match_date']}")
                print(f"  Team: {peter_match['team_name']}")
                print(f"  Division: {peter_match['division']}, Season: {peter_match['season']}")
                print(f"  Teammates: {peter_match['teammate_names']}")
            
            candidates = self.find_matching_peters(peter_match, specific_peters)
            
            if i < 10:
                print(f"  Candidates ({len(candidates)}):")
                for candidate in candidates[:3]:  # Show top 3
                    print(f"    {candidate['player_name']} (confidence: {candidate['confidence']})")
            
            if len(candidates) == 0:
                no_match_count += 1
            elif len(candidates) == 1:
                single_match_count += 1
                splitting_recommendations.append({
                    'sub_match_id': peter_match['sub_match_id'],
                    'from_player_id': peter_match['peter_player_id'],
                    'to_player_id': candidates[0]['player_id'],
                    'to_player_name': candidates[0]['player_name'],
                    'confidence': candidates[0]['confidence'],
                    'match_date': peter_match['match_date'],
                    'context': f"{peter_match['team_name']} ({peter_match['division']}) {peter_match['season']}"
                })
            else:
                multiple_match_count += 1
                # Take the highest confidence candidate if confidence > 80
                if candidates[0]['confidence'] >= 80:
                    splitting_recommendations.append({
                        'sub_match_id': peter_match['sub_match_id'],
                        'from_player_id': peter_match['peter_player_id'],
                        'to_player_id': candidates[0]['player_id'],
                        'to_player_name': candidates[0]['player_name'],
                        'confidence': candidates[0]['confidence'],
                        'match_date': peter_match['match_date'],
                        'context': f"{peter_match['team_name']} ({peter_match['division']}) {peter_match['season']}",
                        'note': f"Multiple candidates, chose highest confidence ({candidates[0]['confidence']})"
                    })
        
        print(f"\\n=== Summary ===")
        print(f"Total matches analyzed: {len(peter_matches)}")
        print(f"No matching specific Peter: {no_match_count}")
        print(f"Single candidate: {single_match_count}")
        print(f"Multiple candidates: {multiple_match_count}")
        print(f"Confident recommendations: {len(splitting_recommendations)}")
        
        # Group recommendations by target player
        by_target = defaultdict(list)
        for rec in splitting_recommendations:
            by_target[rec['to_player_name']].append(rec)
        
        print(f"\\n=== Recommended Splits ===")
        for player_name, recs in sorted(by_target.items()):
            print(f"{player_name}: {len(recs)} matches")
            avg_confidence = sum(r['confidence'] for r in recs) / len(recs)
            print(f"  Average confidence: {avg_confidence:.1f}")
        
        return splitting_recommendations
    
    def generate_mapping_sql(self, recommendations):
        """Generate SQL to create the mappings"""
        sql_statements = []
        
        for rec in recommendations:
            sql = f"""
INSERT INTO player_name_mappings (
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
    {rec['from_player_id']}, 
    {rec['to_player_id']}, 
    '{rec['to_player_name']}',
    '{rec['context']}',
    {rec['confidence']}, 
    'first_name_only', 
    'pending',
    1,
    1,
    'Match from {rec['match_date']}: {rec.get('note', 'Auto-generated mapping based on context analysis')}'
);"""
            sql_statements.append(sql.strip())
        
        return sql_statements

if __name__ == "__main__":
    splitter = PeterMatchSplitter()
    recommendations = splitter.analyze_peter_splitting()
    
    if recommendations:
        print(f"\\n=== Generated SQL for {len(recommendations)} mappings ===")
        sql_statements = splitter.generate_mapping_sql(recommendations[:5])  # Show first 5
        for sql in sql_statements:
            print(sql)
            print()