#!/usr/bin/env python3
"""
First Name Analyzer
Analyzes single first names and maps them to full names based on team context

Created: 2025-09-21
"""
import sqlite3
import sys
from collections import defaultdict
from difflib import SequenceMatcher

class FirstNameAnalyzer:
    def __init__(self, db_path="goldenstat.db"):
        self.db_path = db_path
    
    def get_problematic_first_names(self, min_matches=50, min_teams=3):
        """Get first names that likely represent multiple people"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT 
                    p.id,
                    p.name,
                    COUNT(DISTINCT smp.sub_match_id) as matches,
                    COUNT(DISTINCT t.name) as team_count,
                    GROUP_CONCAT(DISTINCT t.name) as teams,
                    MIN(m.match_date) as first_match,
                    MAX(m.match_date) as last_match
                FROM players p
                JOIN sub_match_participants smp ON p.id = smp.player_id
                JOIN sub_matches sm ON smp.sub_match_id = sm.id
                JOIN matches m ON sm.match_id = m.id
                JOIN teams t ON t.id = CASE WHEN smp.team_number = 1 THEN m.team1_id ELSE m.team2_id END
                WHERE p.name NOT LIKE '% %'  -- Only single names
                    AND LENGTH(TRIM(p.name)) > 2  -- At least 3 characters
                    AND NOT EXISTS (
                        SELECT 1 FROM player_mappings pm 
                        WHERE pm.source_player_id = p.id
                    )
                GROUP BY p.id, p.name
                HAVING matches >= ? OR team_count >= ?
                ORDER BY matches DESC, team_count DESC
            """, (min_matches, min_teams))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def analyze_first_name_activity(self, first_name):
        """Detailed analysis of a first name's activity by team and time"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT 
                    smp.sub_match_id,
                    m.match_date,
                    t.name as team_name,
                    strftime('%Y-%m', m.match_date) as year_month,
                    strftime('%Y', m.match_date) as year
                FROM players p
                JOIN sub_match_participants smp ON p.id = smp.player_id
                JOIN sub_matches sm ON smp.sub_match_id = sm.id
                JOIN matches m ON sm.match_id = m.id
                JOIN teams t ON t.id = CASE WHEN smp.team_number = 1 THEN m.team1_id ELSE m.team2_id END
                WHERE p.name = ?
                ORDER BY m.match_date
            """, (first_name,))
            
            activities = [dict(row) for row in cursor.fetchall()]
            
            # Group by team
            team_activities = defaultdict(list)
            for activity in activities:
                team_activities[activity['team_name']].append(activity)
            
            # Analyze each team's activity
            team_analysis = {}
            for team, team_acts in team_activities.items():
                first_date = min(act['match_date'] for act in team_acts)
                last_date = max(act['match_date'] for act in team_acts)
                match_count = len(team_acts)
                
                # Group by year-month to detect activity patterns
                monthly_activity = defaultdict(int)
                for act in team_acts:
                    monthly_activity[act['year_month']] += 1
                
                team_analysis[team] = {
                    'matches': match_count,
                    'first_date': first_date,
                    'last_date': last_date,
                    'monthly_activity': dict(monthly_activity),
                    'years': set(act['year'] for act in team_acts)
                }
            
            return team_analysis
    
    def find_full_name_candidates_for_team(self, first_name, team_name, time_period=None):
        """Find full name candidates for a specific team"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Build query with optional time filter
            time_filter = ""
            params = [team_name, f"{first_name} %"]
            
            if time_period:
                time_filter = "AND m.match_date BETWEEN ? AND ?"
                params.extend([time_period['start'], time_period['end']])
            
            cursor.execute(f"""
                SELECT DISTINCT 
                    p.id,
                    p.name,
                    COUNT(DISTINCT smp.sub_match_id) as matches,
                    MIN(m.match_date) as first_match,
                    MAX(m.match_date) as last_match
                FROM players p
                JOIN sub_match_participants smp ON p.id = smp.player_id
                JOIN sub_matches sm ON smp.sub_match_id = sm.id
                JOIN matches m ON sm.match_id = m.id
                JOIN teams t ON t.id = CASE WHEN smp.team_number = 1 THEN m.team1_id ELSE m.team2_id END
                WHERE t.name = ?
                    AND p.name LIKE ?  -- First name + space + surname
                    AND p.name != ?    -- Not the generic first name
                    {time_filter}
                    AND NOT EXISTS (
                        SELECT 1 FROM player_mappings pm 
                        WHERE pm.target_player_id = p.id
                    )
                GROUP BY p.id, p.name
                ORDER BY matches DESC
            """, params + [first_name])
            
            candidates = []
            for row in cursor.fetchall():
                candidate = dict(row)
                
                # Calculate name similarity
                full_name_parts = candidate['name'].split()
                if len(full_name_parts) >= 2:
                    first_word = full_name_parts[0]
                    similarity = SequenceMatcher(None, 
                        first_name.lower().strip(), 
                        first_word.lower().strip()
                    ).ratio()
                    candidate['similarity'] = similarity
                    
                    if similarity >= 0.8:  # High similarity threshold
                        candidates.append(candidate)
            
            return candidates
    
    def suggest_safe_mappings(self, first_name, min_team_matches=10):
        """Suggest safe mappings for a first name based on team context"""
        print(f"🔍 Analyzing '{first_name}' for safe mappings...")
        
        team_analysis = self.analyze_first_name_activity(first_name)
        suggestions = []
        
        for team_name, analysis in team_analysis.items():
            if analysis['matches'] < min_team_matches:
                continue
                
            print(f"\n📊 Team: {team_name}")
            print(f"   Matches: {analysis['matches']}")
            print(f"   Period: {analysis['first_date'][:10]} to {analysis['last_date'][:10]}")
            print(f"   Years: {sorted(analysis['years'])}")
            
            # Find candidates for this team
            candidates = self.find_full_name_candidates_for_team(first_name, team_name)
            
            if not candidates:
                print(f"   ❌ No full name candidates found")
                continue
            
            print(f"   💡 Found {len(candidates)} candidate(s):")
            
            best_candidate = None
            for candidate in candidates:
                print(f"     - '{candidate['name']}' (similarity: {candidate['similarity']:.2f})")
                print(f"       {candidate['matches']} matches, {candidate['first_match'][:10]} to {candidate['last_match'][:10]}")
                
                # Check for temporal overlap
                candidate_years = set()
                for year in range(int(candidate['first_match'][:4]), int(candidate['last_match'][:4]) + 1):
                    candidate_years.add(str(year))
                
                overlap = analysis['years'].intersection(candidate_years)
                if overlap:
                    print(f"       ✅ Temporal overlap: {sorted(overlap)}")
                    
                    # This is a good candidate
                    if not best_candidate or candidate['matches'] > best_candidate['matches']:
                        best_candidate = candidate
                else:
                    print(f"       ⚠️  No temporal overlap")
            
            if best_candidate:
                suggestions.append({
                    'first_name': first_name,
                    'team_name': team_name,
                    'team_matches': analysis['matches'],
                    'full_name': best_candidate['name'],
                    'full_name_matches': best_candidate['matches'],
                    'similarity': best_candidate['similarity'],
                    'confidence': 'high' if best_candidate['similarity'] >= 0.95 else 'medium'
                })
                print(f"   🎯 SUGGESTION: Map '{first_name}' in {team_name} → '{best_candidate['name']}'")
        
        return suggestions
    
    def batch_analyze_problematic_names(self, limit=10):
        """Analyze multiple problematic first names"""
        problematic = self.get_problematic_first_names()
        
        if limit:
            problematic = problematic[:limit]
        
        print(f"🔍 Analyzing {len(problematic)} problematic first names...")
        print()
        
        all_suggestions = []
        
        for player in problematic:
            suggestions = self.suggest_safe_mappings(player['name'])
            all_suggestions.extend(suggestions)
            print("\n" + "="*80)
        
        return all_suggestions
    
    def create_mapping_suggestions(self, suggestions, dry_run=True):
        """Create mapping suggestions in the database"""
        from player_mapping_manager import PlayerMappingManager
        
        mapping_manager = PlayerMappingManager(self.db_path)
        created_count = 0
        
        print(f"{'🔍 DRY RUN - Would create' if dry_run else '📝 Creating'} {len(suggestions)} mapping suggestions...")
        
        for suggestion in suggestions:
            confidence = 90 if suggestion['confidence'] == 'high' else 80
            
            if not dry_run:
                success, message = mapping_manager.create_mapping_suggestion(
                    suggestion['first_name'],
                    suggestion['full_name'],
                    "substring_match",
                    confidence
                )
                
                if success:
                    created_count += 1
                    print(f"   ✅ {message}")
                else:
                    print(f"   ❌ {message}")
            else:
                print(f"   📝 Would map: '{suggestion['first_name']}' → '{suggestion['full_name']}' (team: {suggestion['team_name']})")
                created_count += 1
        
        return created_count

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 first_name_analyzer.py <command> [args...]")
        print("")
        print("Commands:")
        print("  list [min_matches] [min_teams]     - List problematic first names (default: 50, 3)")
        print("  analyze <first_name>               - Analyze specific first name")
        print("  batch [limit]                      - Batch analyze problematic names (default: 10)")
        print("  suggest <first_name>               - Get mapping suggestions for first name")
        print("  create-mappings [limit] [--force]  - Create mapping suggestions")
        print("")
        print("Examples:")
        print("  python3 first_name_analyzer.py list 30 2")
        print("  python3 first_name_analyzer.py analyze Micke")
        print("  python3 first_name_analyzer.py suggest Johan")
        print("  python3 first_name_analyzer.py create-mappings 5 --force")
        return 1
    
    analyzer = FirstNameAnalyzer()
    command = sys.argv[1]
    
    if command == "list":
        min_matches = int(sys.argv[2]) if len(sys.argv) > 2 else 50
        min_teams = int(sys.argv[3]) if len(sys.argv) > 3 else 3
        
        problematic = analyzer.get_problematic_first_names(min_matches, min_teams)
        print(f"📋 {len(problematic)} problematic first names:")
        for player in problematic:
            print(f"   {player['name']}: {player['matches']} matches, {player['team_count']} teams")
    
    elif command == "analyze":
        if len(sys.argv) < 3:
            print("Usage: analyze <first_name>")
            return 1
        first_name = sys.argv[2]
        
        team_analysis = analyzer.analyze_first_name_activity(first_name)
        print(f"📊 Activity analysis for '{first_name}':")
        for team, analysis in team_analysis.items():
            print(f"   {team}: {analysis['matches']} matches ({analysis['first_date'][:10]} - {analysis['last_date'][:10]})")
    
    elif command == "suggest":
        if len(sys.argv) < 3:
            print("Usage: suggest <first_name>")
            return 1
        first_name = sys.argv[2]
        analyzer.suggest_safe_mappings(first_name)
    
    elif command == "batch":
        limit = int(sys.argv[2]) if len(sys.argv) > 2 else 10
        analyzer.batch_analyze_problematic_names(limit)
    
    elif command == "create-mappings":
        limit = int(sys.argv[2]) if len(sys.argv) > 2 and sys.argv[2].isdigit() else 10
        force = "--force" in sys.argv
        
        suggestions = analyzer.batch_analyze_problematic_names(limit)
        created_count = analyzer.create_mapping_suggestions(suggestions, dry_run=not force)
        
        if not force:
            print(f"\n💡 Use --force to actually create {created_count} mapping suggestions")
    
    else:
        print(f"Unknown command: {command}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())