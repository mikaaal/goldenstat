#!/usr/bin/env python3
"""
Player Duplicate Detection Script
Finds potential duplicate player registrations within clubs/teams

Created: 2025-09-19
"""
import sqlite3
import sys
import re
from collections import defaultdict
from difflib import SequenceMatcher
import json
from datetime import datetime

class DuplicatePlayerFinder:
    def __init__(self, db_path="goldenstat.db"):
        self.db_path = db_path
        
    def normalize_name(self, name):
        """Normalize a name for comparison - remove extra spaces, fix case"""
        if not name:
            return ""
        # Convert to lowercase, remove extra spaces, strip
        normalized = ' '.join(name.lower().strip().split())
        return normalized
    
    def get_name_variants(self, name):
        """Generate potential variants of a name for matching"""
        variants = set()
        
        # Original name
        variants.add(name.strip())
        
        # Lowercase version
        variants.add(name.lower().strip())
        
        # Title case version
        variants.add(name.title().strip())
        
        # First name only (if multiple words)
        words = name.strip().split()
        if len(words) > 1:
            variants.add(words[0])
            variants.add(words[0].lower())
            variants.add(words[0].title())
        
        # Remove middle initials/names (assume first and last are most important)
        if len(words) >= 3:
            variants.add(f"{words[0]} {words[-1]}")
            variants.add(f"{words[0]} {words[-1]}".lower())
            variants.add(f"{words[0]} {words[-1]}".title())
        
        return variants
    
    def similarity_score(self, name1, name2):
        """Calculate similarity between two names (0-1, 1 = identical)"""
        # Normalize both names
        norm1 = self.normalize_name(name1)
        norm2 = self.normalize_name(name2)
        
        # Exact match after normalization
        if norm1 == norm2:
            return 1.0
        
        # Use sequence matcher for similarity
        return SequenceMatcher(None, norm1, norm2).ratio()
    
    def get_players_by_team(self, team_pattern=None):
        """Get all players grouped by teams they've played for"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Build query with optional team filter
            where_clause = ""
            params = []
            if team_pattern:
                where_clause = "WHERE t.name LIKE ?"
                params = [f"%{team_pattern}%"]
            
            cursor.execute(f"""
                SELECT 
                    p.id as player_id,
                    p.name as player_name,
                    t.name as team_name,
                    COUNT(DISTINCT smp.sub_match_id) as match_count,
                    MIN(m.match_date) as first_match,
                    MAX(m.match_date) as last_match
                FROM players p
                JOIN sub_match_participants smp ON p.id = smp.player_id
                JOIN sub_matches sm ON smp.sub_match_id = sm.id
                JOIN matches m ON sm.match_id = m.id
                JOIN teams t ON t.id = CASE WHEN smp.team_number = 1 THEN m.team1_id ELSE m.team2_id END
                {where_clause}
                GROUP BY p.id, p.name, t.name
                HAVING COUNT(DISTINCT smp.sub_match_id) >= 1
                ORDER BY t.name, p.name
            """, params)
            
            results = defaultdict(list)
            for row in cursor.fetchall():
                team_name = row['team_name']
                results[team_name].append(dict(row))
            
            return results
    
    def find_duplicates_in_team(self, team_name, players):
        """Find potential duplicates within a single team"""
        duplicates = []
        
        # Compare each player with every other player in the team
        for i, player1 in enumerate(players):
            for j, player2 in enumerate(players[i+1:], i+1):
                similarity = self.similarity_score(player1['player_name'], player2['player_name'])
                
                # Different thresholds for different types of matches
                is_duplicate = False
                match_type = ""
                
                # Exact match after normalization
                if self.normalize_name(player1['player_name']) == self.normalize_name(player2['player_name']):
                    is_duplicate = True
                    match_type = "case_difference"
                
                # Very high similarity (likely typos)
                elif similarity >= 0.85:
                    is_duplicate = True
                    match_type = "high_similarity"
                
                # Check if one name is contained in the other (nickname/full name)
                elif (self.normalize_name(player1['player_name']) in self.normalize_name(player2['player_name']) or
                      self.normalize_name(player2['player_name']) in self.normalize_name(player1['player_name'])):
                    # Only if the shorter name is at least 3 characters
                    shorter_name = min(player1['player_name'], player2['player_name'], key=len)
                    if len(shorter_name.strip()) >= 3:
                        is_duplicate = True
                        match_type = "substring_match"
                
                # Check for first name only matches
                elif len(player1['player_name'].split()) == 1 or len(player2['player_name'].split()) == 1:
                    # One is a single name, check if it matches the first word of the other
                    words1 = player1['player_name'].strip().split()
                    words2 = player2['player_name'].strip().split()
                    
                    if (len(words1) == 1 and len(words2) > 1 and 
                        self.normalize_name(words1[0]) == self.normalize_name(words2[0])):
                        is_duplicate = True
                        match_type = "first_name_only"
                    elif (len(words2) == 1 and len(words1) > 1 and 
                          self.normalize_name(words2[0]) == self.normalize_name(words1[0])):
                        is_duplicate = True
                        match_type = "first_name_only"
                
                if is_duplicate:
                    duplicates.append({
                        'team_name': team_name,
                        'player1': player1,
                        'player2': player2,
                        'similarity': similarity,
                        'match_type': match_type
                    })
        
        return duplicates
    
    def generate_report(self, team_pattern=None, output_file=None):
        """Generate a comprehensive duplicate report"""
        print(f"🔍 Analyzing player duplicates...")
        if team_pattern:
            print(f"   Filtering teams containing: '{team_pattern}'")
        
        # Get all players by team
        teams_data = self.get_players_by_team(team_pattern)
        
        all_duplicates = []
        total_teams = len(teams_data)
        
        for i, (team_name, players) in enumerate(teams_data.items(), 1):
            print(f"   [{i}/{total_teams}] Analyzing {team_name} ({len(players)} players)")
            
            team_duplicates = self.find_duplicates_in_team(team_name, players)
            all_duplicates.extend(team_duplicates)
        
        # Generate report
        report = {
            'generated_at': datetime.now().isoformat(),
            'team_filter': team_pattern,
            'summary': {
                'total_teams_analyzed': total_teams,
                'total_potential_duplicates': len(all_duplicates),
                'teams_with_duplicates': len(set(d['team_name'] for d in all_duplicates))
            },
            'duplicates_by_type': {},
            'duplicates': all_duplicates
        }
        
        # Group by match type
        for duplicate in all_duplicates:
            match_type = duplicate['match_type']
            if match_type not in report['duplicates_by_type']:
                report['duplicates_by_type'][match_type] = 0
            report['duplicates_by_type'][match_type] += 1
        
        # Print summary
        print(f"\n📊 Analysis complete!")
        print(f"   Teams analyzed: {report['summary']['total_teams_analyzed']}")
        print(f"   Potential duplicates found: {report['summary']['total_potential_duplicates']}")
        print(f"   Teams with duplicates: {report['summary']['teams_with_duplicates']}")
        
        print(f"\n📋 Duplicates by type:")
        for match_type, count in report['duplicates_by_type'].items():
            print(f"   {match_type}: {count}")
        
        # Save to file if specified
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            print(f"\n💾 Report saved to: {output_file}")
        
        return report
    
    def print_duplicates_for_team(self, team_pattern, limit=None):
        """Print a human-readable list of duplicates for teams matching pattern"""
        teams_data = self.get_players_by_team(team_pattern)
        
        total_duplicates = 0
        
        for team_name, players in teams_data.items():
            duplicates = self.find_duplicates_in_team(team_name, players)
            if not duplicates:
                continue
                
            print(f"\n🏆 {team_name}")
            print(f"   {len(duplicates)} potential duplicate(s) found:")
            
            for i, dup in enumerate(duplicates):
                if limit and i >= limit:
                    print(f"   ... and {len(duplicates) - limit} more")
                    break
                    
                p1 = dup['player1']
                p2 = dup['player2']
                print(f"   {i+1}. '{p1['player_name']}' vs '{p2['player_name']}'")
                print(f"      Type: {dup['match_type']}, Similarity: {dup['similarity']:.2f}")
                print(f"      Player 1: {p1['match_count']} matches, {p1['first_match']} to {p1['last_match']}")
                print(f"      Player 2: {p2['match_count']} matches, {p2['first_match']} to {p2['last_match']}")
                print()
            
            total_duplicates += len(duplicates)
        
        print(f"\n📊 Total potential duplicates: {total_duplicates}")

def main():
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python3 find_duplicate_players.py <team_pattern> [output_file]")
        print("Example: python3 find_duplicate_players.py Dartanjang")
        print("Example: python3 find_duplicate_players.py Dartanjang dartanjang_duplicates.json")
        return 1
    
    team_pattern = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None
    
    finder = DuplicatePlayerFinder()
    
    # Generate full report
    if output_file:
        finder.generate_report(team_pattern, output_file)
    
    # Print human-readable summary
    finder.print_duplicates_for_team(team_pattern, limit=5)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())