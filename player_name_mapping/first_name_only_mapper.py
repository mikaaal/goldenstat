#!/usr/bin/env python3
"""
First Name Only Mapper
Finds all players with only first names and maps them to full-name players
using the same temporal-aware logic as the Peter splitter.

Created: 2025-09-22
"""
import sqlite3
from collections import defaultdict
from datetime import datetime
import re

class FirstNameOnlyMapper:
    def __init__(self, db_path="../goldenstat.db"):
        self.db_path = db_path
    
    def extract_club_name(self, team_name):
        """Extract club name from 'Club (Division)' format"""
        if '(' in team_name:
            return team_name.split('(')[0].strip()
        return team_name.strip()
    
    def find_first_name_only_players(self):
        """Find all players who are registered with only a first name"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Find players with short names that don't contain spaces
            # and have participated in matches (so they're worth mapping)
            query = """
            SELECT DISTINCT p.id, p.name, COUNT(DISTINCT smp.sub_match_id) as match_count
            FROM players p
            JOIN sub_match_participants smp ON p.id = smp.player_id
            WHERE LENGTH(p.name) <= 15  -- Reasonable first name length
                AND p.name NOT LIKE '% %'  -- No spaces (no last name)
                AND p.name NOT LIKE '%(%'  -- No parentheses
                AND p.name NOT LIKE '%.%'  -- No abbreviations like "P."
                AND LENGTH(p.name) >= 3    -- At least 3 characters
                AND p.name NOT IN ('Peter') -- Exclude Peter (already handled)
            GROUP BY p.id, p.name
            HAVING match_count >= 3  -- Only players with multiple matches
            ORDER BY match_count DESC, p.name
            """
            
            cursor.execute(query)
            return cursor.fetchall()
    
    def find_potential_full_name_matches(self, first_name):
        """Find players with full names that start with the given first name"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Find players whose name starts with the first name + space
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
                COUNT(DISTINCT sm.id) as match_count,
                GROUP_CONCAT(DISTINCT m.match_date ORDER BY m.match_date) as all_dates
                
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
                t.name as team_name,
                smp.team_number,
                p.id as player_id,
                p.name as player_name
                
            FROM players p
            JOIN sub_match_participants smp ON p.id = smp.player_id
            JOIN sub_matches sm ON smp.sub_match_id = sm.id
            JOIN matches m ON sm.match_id = m.id
            JOIN teams t ON (
                CASE WHEN smp.team_number = 1 THEN m.team1_id ELSE m.team2_id END
            ) = t.id
            
            WHERE p.id = ?
            ORDER BY m.match_date
            """
            
            cursor.execute(query, (first_name_player_id,))
            return cursor.fetchall()
    
    def find_best_temporal_match(self, first_name_match, potential_full_names_timelines):
        """Find best temporal match using same logic as Peter splitter"""
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
    
    def analyze_first_name_player(self, first_name_player):
        """Analyze a specific first-name player for potential mappings"""
        first_name = first_name_player['name']
        player_id = first_name_player['id']
        
        print(f"\\n=== Analyzing '{first_name}' (ID: {player_id}, {first_name_player['match_count']} matches) ===")
        
        # Find potential full-name matches
        potential_matches = self.find_potential_full_name_matches(first_name)
        
        if not potential_matches:
            print(f"  No potential full-name matches found for '{first_name}'")
            return []
        
        print(f"  Found {len(potential_matches)} potential full-name matches:")
        for match in potential_matches:
            print(f"    {match['name']} ({match['match_count']} matches)")
        
        # Get timelines for all potential matches
        all_timelines = []
        for potential_match in potential_matches:
            timelines = self.get_player_context_timeline(potential_match['id'])
            all_timelines.extend(timelines)
        
        # Get all first-name matches
        first_name_matches = self.get_first_name_matches_with_context(player_id)
        
        print(f"\\n  Analyzing {len(first_name_matches)} '{first_name}' matches...")
        
        mappings = []
        conflicts = []
        
        # Analyze each first-name match
        for i, fn_match in enumerate(first_name_matches):
            best_match = self.find_best_temporal_match(fn_match, all_timelines)
            
            if i < 5:  # Show first 5 for debugging
                print(f"\\n    Match {i+1}: {fn_match['match_date'][:10]}")
                print(f"      Context: {fn_match['team_name']} ({fn_match['division']}) {fn_match['season']}")
                
                if best_match:
                    print(f"      → {best_match['player_name']} (score: {best_match['total_score']})")
                    print(f"        {best_match['reasoning']}")
                else:
                    print(f"      → No suitable match found")
            
            if best_match and best_match['total_score'] >= 80:
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
            else:
                conflicts.append({
                    'sub_match_id': fn_match['sub_match_id'],
                    'first_name': first_name,
                    'date': fn_match['match_date'],
                    'context': f"{fn_match['team_name']} ({fn_match['division']}) {fn_match['season']}",
                    'best_candidate': best_match['player_name'] if best_match else None,
                    'best_score': best_match['total_score'] if best_match else 0
                })
        
        # Summarize results for this first name
        by_target = defaultdict(list)
        for mapping in mappings:
            by_target[mapping['target_player_name']].append(mapping)
        
        print(f"\\n  Results for '{first_name}':")
        print(f"    Successfully mapped: {len(mappings)}/{len(first_name_matches)} matches")
        
        if by_target:
            print(f"    Mappings by target:")
            for target_name, target_mappings in sorted(by_target.items()):
                avg_conf = sum(m['confidence'] for m in target_mappings) / len(target_mappings)
                date_range = f"{min(m['match_date'] for m in target_mappings)[:10]} to {max(m['match_date'] for m in target_mappings)[:10]}"
                print(f"      {target_name}: {len(target_mappings)} matches (avg conf: {avg_conf:.1f}) [{date_range}]")
        
        if conflicts:
            print(f"    Conflicts: {len(conflicts)} matches need manual review")
        
        return mappings
    
    def analyze_all_first_name_players(self):
        """Main analysis function for all first-name players"""
        print("=== First Name Only Player Mapping Analysis ===\\n")
        
        # Find all first-name-only players
        first_name_players = self.find_first_name_only_players()
        
        print(f"Found {len(first_name_players)} first-name-only players with 3+ matches:")
        for player in first_name_players[:10]:  # Show top 10
            print(f"  {player['name']}: {player['match_count']} matches")
        
        if len(first_name_players) > 10:
            print(f"  ... and {len(first_name_players) - 10} more")
        
        all_mappings = []
        
        # Analyze each first-name player
        for i, first_name_player in enumerate(first_name_players[:20]):  # Limit to first 20 for now
            mappings = self.analyze_first_name_player(first_name_player)
            all_mappings.extend(mappings)
            
            if i >= 4:  # Show detailed analysis for first 5 only
                print(f"\\n=== {first_name_player['name']} (ID: {first_name_player['id']}) ===")
                print(f"  Analyzed {first_name_player['match_count']} matches, found {len(mappings)} mappings")
        
        print(f"\\n=== Overall Summary ===")
        print(f"Analyzed {min(20, len(first_name_players))} first-name players")
        print(f"Generated {len(all_mappings)} potential mappings")
        
        # Group by first name
        by_first_name = defaultdict(list)
        for mapping in all_mappings:
            by_first_name[mapping['first_name']].append(mapping)
        
        print(f"\\nSuccessful mappings by first name:")
        for first_name, mappings in sorted(by_first_name.items(), key=lambda x: len(x[1]), reverse=True):
            if mappings:
                avg_conf = sum(m['confidence'] for m in mappings) / len(mappings)
                targets = set(m['target_player_name'] for m in mappings)
                print(f"  {first_name}: {len(mappings)} mappings to {len(targets)} targets (avg conf: {avg_conf:.1f})")
        
        return all_mappings

if __name__ == "__main__":
    mapper = FirstNameOnlyMapper()
    mappings = mapper.analyze_all_first_name_players()