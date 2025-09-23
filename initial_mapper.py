#!/usr/bin/env python3
"""
Initial Letter Surname Mapper
Finds players with abbreviated surnames (First N) and matches them to full names in same teams

Created: 2025-09-21
"""
import sqlite3
import sys
from difflib import SequenceMatcher
from player_mapping_manager import PlayerMappingManager

class InitialMapper:
    def __init__(self, db_path="goldenstat.db"):
        self.db_path = db_path
        self.mapping_manager = PlayerMappingManager(db_path)
    
    def get_initial_surname_players(self, min_matches=2):
        """Get all players with first name + single letter surname"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT 
                    p.id,
                    p.name,
                    COUNT(DISTINCT smp.sub_match_id) as match_count
                FROM players p
                JOIN sub_match_participants smp ON p.id = smp.player_id
                WHERE p.name REGEXP '^[A-Za-zÅÄÖåäö]+ [A-Za-zÅÄÖåäö]$'
                    AND NOT EXISTS (
                        SELECT 1 FROM player_mappings pm 
                        WHERE pm.source_player_id = p.id
                    )
                GROUP BY p.id, p.name
                HAVING COUNT(DISTINCT smp.sub_match_id) >= ?
                ORDER BY match_count DESC
            """, (min_matches,))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def get_player_teams(self, player_name):
        """Get all teams a player has played for"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT DISTINCT 
                    t.name as team_name,
                    COUNT(DISTINCT smp.sub_match_id) as matches,
                    MIN(m.match_date) as first_match,
                    MAX(m.match_date) as last_match
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
    
    def find_full_name_candidates(self, short_name, team_contexts):
        """Find potential full name matches in same teams"""
        # Extract first name and initial
        parts = short_name.strip().split()
        if len(parts) != 2:
            return []
        
        first_name = parts[0]
        initial = parts[1].upper()
        
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Get team names
            team_names = [ctx['team_name'] for ctx in team_contexts]
            team_placeholders = ','.join(['?' for _ in team_names])
            
            # Find players with full surnames starting with the initial
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
                    AND p.name LIKE ?      -- First name match
                    AND p.name LIKE ?      -- Surname starts with initial + more chars
                    AND p.name != ?        -- Not the same player
                    AND NOT EXISTS (
                        SELECT 1 FROM player_mappings pm 
                        WHERE pm.target_player_id = p.id
                    )
                GROUP BY p.id, p.name, t.name
                ORDER BY matches DESC
            """, team_names + [f"{first_name} {initial}%", f"{first_name} {initial}__%", short_name])
            
            candidates = []
            for row in cursor.fetchall():
                candidate = dict(row)
                
                # Calculate similarity for the full names
                similarity = SequenceMatcher(None, 
                    short_name.lower().strip(), 
                    candidate['name'].lower().strip()
                ).ratio()
                
                candidate['similarity'] = similarity
                candidates.append(candidate)
            
            return sorted(candidates, key=lambda x: (x['matches'], x['similarity']), reverse=True)
    
    def analyze_initial_player(self, player_name):
        """Analyze a specific initial-surname player"""
        print(f"🔍 Analyzing player: {player_name}")
        
        # Get team context
        team_contexts = self.get_player_teams(player_name)
        
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
    
    def batch_analyze(self, limit=20, min_matches=5, dry_run=True):
        """Batch analyze initial surname players"""
        print(f"🔍 Batch analyzing initial surname players...")
        print(f"   Limit: {limit}")
        print(f"   Minimum matches: {min_matches}")
        print(f"   Dry run: {dry_run}")
        print()
        
        players = self.get_initial_surname_players(min_matches)
        
        if limit:
            players = players[:limit]
        
        suggestions_made = 0
        total_candidates = 0
        
        for player in players:
            candidates = self.analyze_initial_player(player['name'])
            
            if candidates:
                total_candidates += len(candidates)
                
                # Take the best candidate (most matches, then highest similarity)
                best_candidate = candidates[0]
                
                if best_candidate['matches'] >= 3:  # Reasonable activity threshold
                    if not dry_run:
                        success, message = self.mapping_manager.create_mapping_suggestion(
                            player['name'], 
                            best_candidate['name'],
                            "initial_expansion",
                            85  # High confidence for this type of mapping
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
                    print(f"   ⚠️  Best candidate has too few matches: {best_candidate['matches']}")
            
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
        print("Usage: python3 initial_mapper.py <command> [args...]")
        print("")
        print("Commands:")
        print("  list [min_matches]          - List initial surname players (default: 2)")
        print("  analyze <name>              - Analyze specific player")
        print("  batch [limit] [min_matches] - Batch analyze (default: 20, 5)")
        print("  create [limit] [min_matches] - Create mappings (default: 20, 5)")
        print("")
        print("Examples:")
        print("  python3 initial_mapper.py list 5")
        print("  python3 initial_mapper.py analyze 'Edwin Å'")
        print("  python3 initial_mapper.py batch 10 5")
        print("  python3 initial_mapper.py create 10 5")
        return 1
    
    mapper = InitialMapper()
    command = sys.argv[1]
    
    if command == "list":
        min_matches = int(sys.argv[2]) if len(sys.argv) > 2 else 2
        
        players = mapper.get_initial_surname_players(min_matches)
        print(f"📋 {len(players)} initial surname players (≥{min_matches} matches):")
        for player in players:
            print(f"   {player['name']}: {player['match_count']} matches")
    
    elif command == "analyze":
        if len(sys.argv) < 3:
            print("Usage: analyze <player_name>")
            return 1
        player_name = sys.argv[2]
        mapper.analyze_initial_player(player_name)
    
    elif command == "batch":
        limit = int(sys.argv[2]) if len(sys.argv) > 2 else 20
        min_matches = int(sys.argv[3]) if len(sys.argv) > 3 else 5
        mapper.batch_analyze(limit, min_matches, dry_run=True)
    
    elif command == "create":
        limit = int(sys.argv[2]) if len(sys.argv) > 2 else 20
        min_matches = int(sys.argv[3]) if len(sys.argv) > 3 else 5
        mapper.batch_analyze(limit, min_matches, dry_run=False)
    
    else:
        print(f"Unknown command: {command}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())