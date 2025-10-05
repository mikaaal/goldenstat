#!/usr/bin/env python3
"""
Temporal-Aware Peter Splitter
Improved logic that considers date ranges and temporal overlaps when mapping
generic "Peter" matches to specific Peters.

Created: 2025-09-22
"""
import sqlite3
from collections import defaultdict
from datetime import datetime, timedelta
import json

class TemporalAwareSplitter:
    def __init__(self, db_path="../goldenstat.db"):
        self.db_path = db_path
    
    def extract_club_name(self, team_name):
        """Extract club name from 'Club (Division)' format"""
        if '(' in team_name:
            return team_name.split('(')[0].strip()
        return team_name.strip()
    
    def get_peter_matches_with_dates(self):
        """Get all Peter matches with detailed date and context info"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            query = """
            SELECT 
                sm.id as sub_match_id,
                m.match_date,
                m.season,
                m.division,
                t.name as team_name,
                smp.team_number,
                p.id as peter_player_id
                
            FROM players p
            JOIN sub_match_participants smp ON p.id = smp.player_id
            JOIN sub_matches sm ON smp.sub_match_id = sm.id
            JOIN matches m ON sm.match_id = m.id
            JOIN teams t ON (
                CASE WHEN smp.team_number = 1 THEN m.team1_id ELSE m.team2_id END
            ) = t.id
            
            WHERE p.name = 'Peter'
            ORDER BY m.match_date
            """
            
            cursor.execute(query)
            return cursor.fetchall()
    
    def get_specific_peters_timelines(self):
        """Get detailed timelines for all specific Peters by club context"""
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
                GROUP_CONCAT(DISTINCT m.match_date) as all_dates
                
            FROM players p
            JOIN sub_match_participants smp ON p.id = smp.player_id
            JOIN sub_matches sm ON smp.sub_match_id = sm.id
            JOIN matches m ON sm.match_id = m.id
            JOIN teams t ON (
                CASE WHEN smp.team_number = 1 THEN m.team1_id ELSE m.team2_id END
            ) = t.id
            
            WHERE p.name LIKE 'Peter %' 
                AND LENGTH(p.name) > 6
            GROUP BY p.id, p.name, t.name, m.division, m.season
            ORDER BY p.name, m.season, m.division
            """
            
            cursor.execute(query)
            return cursor.fetchall()
    
    def find_best_temporal_match(self, peter_match, specific_peters_timelines):
        """
        Find the best specific Peter for a match based on temporal proximity
        and context matching
        """
        peter_club = self.extract_club_name(peter_match['team_name'])
        peter_division = peter_match['division']
        peter_season = peter_match['season']
        peter_date = peter_match['match_date']
        
        candidates = []
        
        # Filter to same club/division/season first
        relevant_timelines = [
            timeline for timeline in specific_peters_timelines
            if (self.extract_club_name(timeline['team_name']).lower() == peter_club.lower() and
                timeline['division'] == peter_division and
                timeline['season'] == peter_season)
        ]
        
        if not relevant_timelines:
            # Fallback: same club and season, any division
            relevant_timelines = [
                timeline for timeline in specific_peters_timelines
                if (self.extract_club_name(timeline['team_name']).lower() == peter_club.lower() and
                    timeline['season'] == peter_season)
            ]
        
        for timeline in relevant_timelines:
            # Calculate temporal proximity score
            first_date = timeline['first_match']
            last_date = timeline['last_match']
            
            # Check if Peter match falls within this player's active period
            if first_date <= peter_date <= last_date:
                # Perfect temporal match
                temporal_score = 100
            else:
                # Calculate distance to closest boundary
                date_obj = datetime.fromisoformat(peter_date.replace(' ', 'T'))
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
            
            # Context matching score
            context_score = 0
            if timeline['division'] == peter_division:
                context_score += 30
            if timeline['season'] == peter_season:
                context_score += 20
            
            total_score = temporal_score + context_score
            
            candidates.append({
                'player_id': timeline['player_id'],
                'player_name': timeline['player_name'],
                'timeline': timeline,
                'temporal_score': temporal_score,
                'context_score': context_score,
                'total_score': total_score,
                'days_overlap': 0 if temporal_score < 100 else "PERFECT_MATCH",
                'reasoning': f"Temporal: {temporal_score}, Context: {context_score}"
            })
        
        # Sort by total score, then by temporal score
        candidates.sort(key=lambda x: (x['total_score'], x['temporal_score']), reverse=True)
        
        return candidates[0] if candidates else None
    
    def analyze_peter_temporal_splitting(self):
        """Main analysis with temporal awareness"""
        print("=== Temporal-Aware Peter Splitting Analysis ===\\n")
        
        peter_matches = self.get_peter_matches_with_dates()
        specific_peters_timelines = self.get_specific_peters_timelines()
        
        print(f"Found {len(peter_matches)} Peter sub-matches to analyze")
        print(f"Found {len(specific_peters_timelines)} specific Peter timelines\\n")
        
        # Group specific Peters by club context for analysis
        by_club_context = defaultdict(list)
        for timeline in specific_peters_timelines:
            club = self.extract_club_name(timeline['team_name'])
            key = f"{club}|{timeline['division']}|{timeline['season']}"
            by_club_context[key].append(timeline)
        
        print("=== Specific Peter contexts ===")
        for context, timelines in by_club_context.items():
            club, division, season = context.split('|')
            print(f"\\n{club} ({division}) {season}:")
            for timeline in timelines:
                print(f"  {timeline['player_name']}: {timeline['first_match']} to {timeline['last_match']} ({timeline['match_count']} matches)")
        
        print("\\n=== Temporal Mapping Analysis ===")
        
        mappings = []
        conflicts = []
        
        for i, peter_match in enumerate(peter_matches):
            best_match = self.find_best_temporal_match(peter_match, specific_peters_timelines)
            
            if i < 10:  # Show first 10 for debugging
                print(f"\\nPeter match {i+1}: {peter_match['match_date'][:10]}")
                print(f"  Context: {peter_match['team_name']} ({peter_match['division']}) {peter_match['season']}")
                
                if best_match:
                    print(f"  → {best_match['player_name']} (score: {best_match['total_score']})")
                    print(f"    Temporal: {best_match['temporal_score']}, Context: {best_match['context_score']}")
                    print(f"    Timeline: {best_match['timeline']['first_match']} to {best_match['timeline']['last_match']}")
                else:
                    print(f"  → No suitable match found")
            
            if best_match and best_match['total_score'] >= 80:
                mappings.append({
                    'sub_match_id': peter_match['sub_match_id'],
                    'peter_date': peter_match['match_date'],
                    'peter_context': f"{peter_match['team_name']} ({peter_match['division']}) {peter_match['season']}",
                    'target_player_id': best_match['player_id'],
                    'target_player_name': best_match['player_name'],
                    'confidence': best_match['total_score'],
                    'temporal_score': best_match['temporal_score'],
                    'reasoning': best_match['reasoning']
                })
            else:
                conflicts.append({
                    'sub_match_id': peter_match['sub_match_id'],
                    'date': peter_match['match_date'],
                    'context': f"{peter_match['team_name']} ({peter_match['division']}) {peter_match['season']}",
                    'best_candidate': best_match['player_name'] if best_match else None,
                    'best_score': best_match['total_score'] if best_match else 0
                })
        
        print(f"\\n=== Results Summary ===")
        print(f"Total Peter matches: {len(peter_matches)}")
        print(f"Successfully mapped: {len(mappings)}")
        print(f"Conflicts/Low confidence: {len(conflicts)}")
        
        # Group successful mappings by target player
        by_target = defaultdict(list)
        for mapping in mappings:
            by_target[mapping['target_player_name']].append(mapping)
        
        print(f"\\n=== Successful Mappings by Target Player ===")
        for player_name, player_mappings in sorted(by_target.items()):
            avg_confidence = sum(m['confidence'] for m in player_mappings) / len(player_mappings)
            avg_temporal = sum(m['temporal_score'] for m in player_mappings) / len(player_mappings)
            print(f"{player_name}: {len(player_mappings)} matches")
            print(f"  Avg confidence: {avg_confidence:.1f}, Avg temporal score: {avg_temporal:.1f}")
            
            # Show date range for this player's mappings
            dates = [m['peter_date'] for m in player_mappings]
            print(f"  Peter match dates: {min(dates)[:10]} to {max(dates)[:10]}")
        
        if conflicts:
            print(f"\\n=== Conflicts requiring manual review ===")
            for conflict in conflicts[:5]:  # Show first 5
                print(f"  {conflict['date'][:10]}: {conflict['context']}")
                if conflict['best_candidate']:
                    print(f"    Best candidate: {conflict['best_candidate']} (score: {conflict['best_score']})")
        
        return mappings, conflicts

if __name__ == "__main__":
    splitter = TemporalAwareSplitter()
    mappings, conflicts = splitter.analyze_peter_temporal_splitting()