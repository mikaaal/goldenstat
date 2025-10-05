#!/usr/bin/env python3
"""
Advanced Name Mapper
Finds potential player name mappings using advanced string similarity and context analysis
"""
import sqlite3
import sys
import re
from collections import defaultdict
from difflib import SequenceMatcher
# import jellyfish  # For phonetic matching - optional dependency
from datetime import datetime, timedelta

class AdvancedNameMapper:
    def __init__(self, db_path="goldenstat.db"):
        self.db_path = db_path
    
    def get_name_components(self, name):
        """Extract and normalize name components"""
        # Remove extra spaces and normalize
        clean_name = ' '.join(name.strip().split())
        words = clean_name.split()
        
        return {
            'full_name': clean_name,
            'first_name': words[0] if words else '',
            'last_name': words[-1] if len(words) > 1 else '',
            'word_count': len(words),
            'words': words
        }
    
    def phonetic_similarity(self, name1, name2):
        """Calculate phonetic similarity using simple phonetic rules"""
        # Simple phonetic matching without external dependencies
        def simple_soundex(name):
            if not name:
                return ""
            name = name.upper()
            # Simple consonant mapping
            mappings = {
                'B': 'P', 'F': 'P', 'P': 'P', 'V': 'P',
                'C': 'K', 'G': 'K', 'J': 'K', 'K': 'K', 'Q': 'K', 'S': 'K', 'X': 'K', 'Z': 'K',
                'D': 'T', 'T': 'T',
                'L': 'L',
                'M': 'M', 'N': 'M',
                'R': 'R'
            }
            result = name[0]  # Keep first letter
            for char in name[1:]:
                if char in mappings:
                    result += mappings[char]
                elif char in 'AEIOUYHW':
                    continue  # Skip vowels and some consonants
                else:
                    result += char
            return result[:4].ljust(4, '0')  # Pad to 4 characters
        
        try:
            soundex1 = simple_soundex(name1)
            soundex2 = simple_soundex(name2)
            soundex_match = soundex1 == soundex2
            
            # Simple check for similar pronunciation
            metaphone_match = self.sounds_similar(name1, name2)
            
            return soundex_match, metaphone_match
        except:
            return False, False
    
    def sounds_similar(self, name1, name2):
        """Simple phonetic similarity check"""
        # Remove common silent letters and normalize
        def normalize_phonetic(name):
            name = name.lower()
            # Replace common phonetic equivalents
            replacements = {
                'ph': 'f', 'th': 't', 'ck': 'k', 'ch': 'k',
                'silent_h': '', 'silent_b': '', 'silent_l': ''
            }
            for old, new in replacements.items():
                if old.startswith('silent_'):
                    continue
                name = name.replace(old, new)
            return name
        
        norm1 = normalize_phonetic(name1)
        norm2 = normalize_phonetic(name2)
        
        return SequenceMatcher(None, norm1, norm2).ratio() > 0.8
    
    def find_name_variants(self, target_name, candidates, similarity_threshold=0.7):
        """Find potential variants of a name among candidates"""
        variants = []
        target_components = self.get_name_components(target_name)
        
        for candidate in candidates:
            if candidate['name'] == target_name:
                continue
                
            candidate_components = self.get_name_components(candidate['name'])
            
            # Calculate various similarity scores
            full_similarity = SequenceMatcher(None, 
                target_components['full_name'].lower(), 
                candidate_components['full_name'].lower()).ratio()
            
            # Check for phonetic similarity
            soundex_match, metaphone_match = self.phonetic_similarity(
                target_components['first_name'], candidate_components['first_name'])
            
            # Look for specific patterns
            patterns_found = []
            confidence = 0
            
            # Pattern 1: Same last name, similar first name
            if (target_components['last_name'].lower() == candidate_components['last_name'].lower() and 
                target_components['last_name'] and len(target_components['last_name']) > 2):
                
                first_similarity = SequenceMatcher(None,
                    target_components['first_name'].lower(),
                    candidate_components['first_name'].lower()).ratio()
                
                if first_similarity >= 0.6 or soundex_match or metaphone_match:
                    patterns_found.append("same_lastname_similar_firstname")
                    confidence += 40
                    
                    # Bonus for phonetic match
                    if soundex_match or metaphone_match:
                        confidence += 20
                        patterns_found.append("phonetic_match")
            
            # Pattern 2: One name is substring of another (nickname pattern)
            if (target_components['first_name'].lower() in candidate_components['full_name'].lower() or
                candidate_components['first_name'].lower() in target_components['full_name'].lower()):
                patterns_found.append("substring_match")
                confidence += 30
            
            # Pattern 3: High overall similarity
            if full_similarity >= similarity_threshold:
                patterns_found.append("high_similarity")
                confidence += int(full_similarity * 50)
            
            # Pattern 4: Single character differences (typos)
            if self.is_likely_typo(target_components['full_name'], candidate_components['full_name']):
                patterns_found.append("likely_typo")
                confidence += 35
            
            # Only consider if we found patterns and have reasonable confidence
            if patterns_found and confidence >= 30:
                variants.append({
                    'candidate': candidate,
                    'similarity': full_similarity,
                    'confidence': min(100, confidence),
                    'patterns': patterns_found,
                    'soundex_match': soundex_match,
                    'metaphone_match': metaphone_match
                })
        
        # Sort by confidence, then similarity
        variants.sort(key=lambda x: (x['confidence'], x['similarity']), reverse=True)
        return variants
    
    def is_likely_typo(self, name1, name2):
        """Check if names are likely typos of each other"""
        # Normalize names
        n1 = name1.lower().strip()
        n2 = name2.lower().strip()
        
        # Length difference should be small
        if abs(len(n1) - len(n2)) > 3:
            return False
        
        # Calculate edit distance using SequenceMatcher
        similarity = SequenceMatcher(None, n1, n2).ratio()
        
        # High similarity with small length suggests typo
        return similarity >= 0.8 and abs(len(n1) - len(n2)) <= 2
    
    def get_players_with_context(self, min_matches=1):
        """Get all players with their team context"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT 
                    p.id,
                    p.name,
                    COUNT(DISTINCT smp.sub_match_id) as total_matches,
                    GROUP_CONCAT(DISTINCT t.name) as teams,
                    MIN(m.match_date) as first_match,
                    MAX(m.match_date) as last_match,
                    COUNT(DISTINCT m.season) as seasons_played
                FROM players p
                LEFT JOIN sub_match_participants smp ON p.id = smp.player_id
                LEFT JOIN sub_matches sm ON smp.sub_match_id = sm.id  
                LEFT JOIN matches m ON sm.match_id = m.id
                LEFT JOIN teams t ON t.id = CASE WHEN smp.team_number = 1 THEN m.team1_id ELSE m.team2_id END
                GROUP BY p.id, p.name
                HAVING COUNT(DISTINCT smp.sub_match_id) >= ?
                ORDER BY p.name
            """, (min_matches,))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def find_team_based_variants(self, team_overlap_threshold=0.5):
        """Find name variants within the same teams"""
        print("🔍 Analyzing name variants within teams...")
        
        players = self.get_players_with_context()
        team_players = defaultdict(list)
        
        # Group players by teams they've played for
        for player in players:
            if player['teams']:
                teams = set(player['teams'].split(','))
                for team in teams:
                    team_players[team.strip()].append(player)
        
        all_suggestions = []
        
        for team_name, team_player_list in team_players.items():
            if len(team_player_list) < 2:
                continue
                
            print(f"   Analyzing {team_name} ({len(team_player_list)} players)")
            
            # Compare each player with others in same team
            for i, player in enumerate(team_player_list):
                variants = self.find_name_variants(player['name'], team_player_list[i+1:])
                
                for variant in variants:
                    candidate = variant['candidate']
                    
                    # Check team overlap
                    player_teams = set(player['teams'].split(',')) if player['teams'] else set()
                    candidate_teams = set(candidate['teams'].split(',')) if candidate['teams'] else set()
                    
                    overlap = len(player_teams & candidate_teams)
                    total_teams = len(player_teams | candidate_teams)
                    overlap_ratio = overlap / max(1, total_teams)
                    
                    if overlap_ratio >= team_overlap_threshold:
                        suggestion = {
                            'player1': player,
                            'player2': candidate,
                            'team_overlap': overlap,
                            'team_overlap_ratio': overlap_ratio,
                            'common_teams': list(player_teams & candidate_teams),
                            **variant
                        }
                        all_suggestions.append(suggestion)
        
        # Sort by confidence and team overlap
        all_suggestions.sort(key=lambda x: (x['confidence'], x['team_overlap_ratio']), reverse=True)
        return all_suggestions
    
    def print_suggestions(self, suggestions, limit=20):
        """Print mapping suggestions in a readable format"""
        print(f"\n📋 Found {len(suggestions)} potential name mappings:")
        
        for i, suggestion in enumerate(suggestions[:limit]):
            p1 = suggestion['player1']
            p2 = suggestion['player2']
            
            print(f"\n{i+1}. '{p1['name']}' ↔ '{p2['name']}'")
            print(f"   Confidence: {suggestion['confidence']}%")
            print(f"   Patterns: {', '.join(suggestion['patterns'])}")
            print(f"   Team overlap: {suggestion['team_overlap']}/{len(suggestion['common_teams'])} teams")
            print(f"   Common teams: {', '.join(suggestion['common_teams'])}")
            print(f"   Player 1: {p1['total_matches']} matches ({p1['first_match']} to {p1['last_match']})")
            print(f"   Player 2: {p2['total_matches']} matches ({p2['first_match']} to {p2['last_match']})")
            
            if suggestion['soundex_match'] or suggestion['metaphone_match']:
                print(f"   Phonetic match: Soundex={suggestion['soundex_match']}, Metaphone={suggestion['metaphone_match']}")
        
        if len(suggestions) > limit:
            print(f"\n... and {len(suggestions) - limit} more suggestions")

def main():
    if len(sys.argv) > 1 and sys.argv[1] in ['-h', '--help']:
        print("Usage: python3 advanced_name_mapper.py [options]")
        print("")
        print("Options:")
        print("  --min-matches N    Minimum matches required (default: 1)")
        print("  --team-overlap N   Team overlap threshold 0.0-1.0 (default: 0.5)")
        print("  --limit N          Limit output to N suggestions (default: 20)")
        print("")
        print("Example:")
        print("  python3 advanced_name_mapper.py --min-matches 5 --limit 10")
        return 0
    
    # Parse arguments
    min_matches = 1
    team_overlap = 0.5
    limit = 20
    
    i = 1
    while i < len(sys.argv):
        if sys.argv[i] == '--min-matches' and i + 1 < len(sys.argv):
            min_matches = int(sys.argv[i + 1])
            i += 2
        elif sys.argv[i] == '--team-overlap' and i + 1 < len(sys.argv):
            team_overlap = float(sys.argv[i + 1])
            i += 2
        elif sys.argv[i] == '--limit' and i + 1 < len(sys.argv):
            limit = int(sys.argv[i + 1])
            i += 2
        else:
            i += 1
    
    print(f"🚀 Advanced Name Mapper")
    print(f"   Minimum matches: {min_matches}")
    print(f"   Team overlap threshold: {team_overlap}")
    print(f"   Output limit: {limit}")
    
    mapper = AdvancedNameMapper()
    suggestions = mapper.find_team_based_variants(team_overlap)
    mapper.print_suggestions(suggestions, limit)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())