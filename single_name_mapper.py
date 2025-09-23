#!/usr/bin/env python3
"""
Single Name Player Mapper
Finds players with only first names and matches them against official league data

Created: 2025-09-21
"""
import sqlite3
import sys
from difflib import SequenceMatcher
from player_mapping_manager import PlayerMappingManager

class SingleNameMapper:
    def __init__(self, db_path="goldenstat.db"):
        self.db_path = db_path
        self.mapping_manager = PlayerMappingManager(db_path)
    
    def get_single_name_players(self, limit=None, min_matches=5):
        """Get all unmapped players with only first names"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            query = """
                SELECT 
                    p.id,
                    p.name,
                    COUNT(DISTINCT smp.sub_match_id) as match_count
                FROM players p
                JOIN sub_match_participants smp ON p.id = smp.player_id
                WHERE p.name NOT LIKE '% %' 
                    AND LENGTH(TRIM(p.name)) > 2
                    AND NOT EXISTS (
                        SELECT 1 FROM player_mappings pm 
                        WHERE pm.source_player_id = p.id
                    )
                GROUP BY p.id, p.name
                HAVING COUNT(DISTINCT smp.sub_match_id) >= ?
                ORDER BY match_count DESC
            """
            
            if limit:
                query += f" LIMIT {limit}"
            
            cursor.execute(query, (min_matches,))
            return [dict(row) for row in cursor.fetchall()]
    
    def get_player_team_context(self, player_name):
        """Get detailed team context for a player"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT 
                    t.name as team_name,
                    COUNT(DISTINCT smp.sub_match_id) as matches,
                    MIN(m.match_date) as first_match,
                    MAX(m.match_date) as last_match,
                    GROUP_CONCAT(DISTINCT strftime('%Y', m.match_date)) as seasons
                FROM players p
                JOIN sub_match_participants smp ON p.id = smp.player_id
                JOIN sub_matches sm ON smp.sub_match_id = sm.id
                JOIN matches m ON sm.match_id = m.id
                JOIN teams t ON t.id = CASE WHEN smp.team_number = 1 THEN m.team1_id ELSE m.team2_id END
                WHERE p.name = ?
                GROUP BY t.name
                ORDER BY matches DESC
            """, (player_name,))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def find_full_name_candidates(self, first_name, team_contexts, min_similarity=0.8):
        """Find potential full name matches in the same teams"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Extract team names for search
            team_names = [ctx['team_name'] for ctx in team_contexts]
            team_placeholders = ','.join(['?' for _ in team_names])
            
            # Find players with full names in the same teams
            cursor.execute(f"""
                SELECT DISTINCT 
                    p.id,
                    p.name,
                    t.name as team_name,
                    COUNT(DISTINCT smp.sub_match_id) as matches
                FROM players p
                JOIN sub_match_participants smp ON p.id = smp.player_id
                JOIN sub_matches sm ON smp.sub_match_id = sm.id
                JOIN matches m ON sm.match_id = m.id
                JOIN teams t ON t.id = CASE WHEN smp.team_number = 1 THEN m.team1_id ELSE m.team2_id END
                WHERE t.name IN ({team_placeholders})
                    AND p.name LIKE '% %'  -- Has at least one space (full name)
                    AND p.name LIKE ?      -- Starts with the first name
                    AND NOT EXISTS (
                        SELECT 1 FROM player_mappings pm 
                        WHERE pm.target_player_id = p.id
                    )
                GROUP BY p.id, p.name, t.name
                ORDER BY matches DESC
            """, team_names + [f"{first_name}%"])
            
            candidates = []
            for row in cursor.fetchall():
                candidate = dict(row)
                
                # Calculate similarity between first name and the first word of full name
                full_name_parts = candidate['name'].split()
                if len(full_name_parts) > 0:
                    first_word = full_name_parts[0]
                    similarity = SequenceMatcher(None, 
                        first_name.lower().strip(), 
                        first_word.lower().strip()
                    ).ratio()
                    
                    candidate['similarity'] = similarity
                    
                    if similarity >= min_similarity:
                        candidates.append(candidate)
            
            return sorted(candidates, key=lambda x: (x['similarity'], x['matches']), reverse=True)
    
    def analyze_single_name_player(self, player_name):
        """Analyze a specific single-name player"""
        print(f"🔍 Analyzing player: {player_name}")
        
        # Get team context
        team_contexts = self.get_player_team_context(player_name)
        
        if not team_contexts:
            print(f"   ⚠️  No team context found")
            return []
        
        print(f"   Team contexts:")
        for ctx in team_contexts:
            print(f"     - {ctx['team_name']}: {ctx['matches']} matches ({ctx['first_match'][:4]} - {ctx['last_match'][:4]})")
        
        # Find candidates
        candidates = self.find_full_name_candidates(player_name, team_contexts)
        
        if not candidates:
            print(f"   ❌ No full name candidates found")
            return []
        
        print(f"   💡 Found {len(candidates)} candidate(s):")
        for candidate in candidates:
            print(f"     - '{candidate['name']}' (similarity: {candidate['similarity']:.2f})")
            print(f"       Team: {candidate['team_name']}, Matches: {candidate['matches']}")
        
        return candidates
    
    def create_mapping_from_candidate(self, first_name, full_name, confidence=None):
        """Create a mapping suggestion"""
        if confidence is None:
            # Calculate confidence based on name similarity
            first_word = full_name.split()[0]
            similarity = SequenceMatcher(None, 
                first_name.lower().strip(), 
                first_word.lower().strip()
            ).ratio()
            confidence = min(95, int(similarity * 100))
        
        mapping_type = "first_name_expansion"
        
        success, message = self.mapping_manager.create_mapping_suggestion(
            first_name, full_name, mapping_type, confidence
        )
        
        return success, message
    
    def batch_analyze(self, limit=10, min_matches=10, dry_run=True):
        """Batch analyze single name players"""
        print(f"🔍 Batch analyzing single name players...")
        print(f"   Limit: {limit}")
        print(f"   Minimum matches: {min_matches}")
        print(f"   Dry run: {dry_run}")
        print()
        
        players = self.get_single_name_players(limit, min_matches)
        
        suggestions_made = 0
        total_candidates = 0
        
        for player in players:
            candidates = self.analyze_single_name_player(player['name'])
            
            if candidates:
                total_candidates += len(candidates)
                
                # Take the best candidate (highest similarity and most matches)
                best_candidate = candidates[0]
                
                if best_candidate['similarity'] >= 0.9:  # High confidence threshold
                    if not dry_run:
                        success, message = self.create_mapping_from_candidate(
                            player['name'], 
                            best_candidate['name']
                        )
                        
                        if success:
                            suggestions_made += 1
                            print(f"   ✅ {message}")
                        else:
                            print(f"   ❌ {message}")
                    else:
                        print(f"   📝 Would map: '{player['name']}' → '{best_candidate['name']}'")
                        suggestions_made += 1
                else:
                    print(f"   ⚠️  Best candidate similarity too low: {best_candidate['similarity']:.2f}")
            
            print()
        
        print(f"📊 Summary:")
        print(f"   Players analyzed: {len(players)}")
        print(f"   Total candidates found: {total_candidates}")
        if dry_run:
            print(f"   Would create suggestions: {suggestions_made}")
        else:
            print(f"   Suggestions created: {suggestions_made}")
        
        return suggestions_made

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 single_name_mapper.py <command> [args...]")
        print("")
        print("Commands:")
        print("  list [limit] [min_matches]  - List single name players (default: 20, 5)")
        print("  analyze <name>              - Analyze specific player")
        print("  batch [limit] [min_matches] - Batch analyze (default: 10, 10)")
        print("  create [limit] [min_matches] - Create mappings (default: 10, 10)")
        print("")
        print("Examples:")
        print("  python3 single_name_mapper.py list 10")
        print("  python3 single_name_mapper.py analyze Robban")
        print("  python3 single_name_mapper.py batch 5 15")
        print("  python3 single_name_mapper.py create 5 15")
        return 1
    
    mapper = SingleNameMapper()
    command = sys.argv[1]
    
    if command == "list":
        limit = int(sys.argv[2]) if len(sys.argv) > 2 else 20
        min_matches = int(sys.argv[3]) if len(sys.argv) > 3 else 5
        
        players = mapper.get_single_name_players(limit, min_matches)
        print(f"📋 {len(players)} single name players (≥{min_matches} matches):")
        for player in players:
            print(f"   {player['name']}: {player['match_count']} matches")
    
    elif command == "analyze":
        if len(sys.argv) < 3:
            print("Usage: analyze <player_name>")
            return 1
        player_name = sys.argv[2]
        mapper.analyze_single_name_player(player_name)
    
    elif command == "batch":
        limit = int(sys.argv[2]) if len(sys.argv) > 2 else 10
        min_matches = int(sys.argv[3]) if len(sys.argv) > 3 else 10
        mapper.batch_analyze(limit, min_matches, dry_run=True)
    
    elif command == "create":
        limit = int(sys.argv[2]) if len(sys.argv) > 2 else 10
        min_matches = int(sys.argv[3]) if len(sys.argv) > 3 else 10
        mapper.batch_analyze(limit, min_matches, dry_run=False)
    
    else:
        print(f"Unknown command: {command}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())