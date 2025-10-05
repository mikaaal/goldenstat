#!/usr/bin/env python3
"""
Player Splitter
Splits problematic single first names into separate players based on team context

Created: 2025-09-21
"""
import sqlite3
import sys
from collections import defaultdict
from first_name_analyzer import FirstNameAnalyzer

class PlayerSplitter:
    def __init__(self, db_path="goldenstat.db"):
        self.db_path = db_path
        self.analyzer = FirstNameAnalyzer(db_path)
    
    def get_unmapped_problematic_names(self, min_matches=20, min_teams=2):
        """Get first names that are still problematic after mappings"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT 
                    p.id,
                    p.name,
                    COUNT(DISTINCT smp.sub_match_id) as matches,
                    COUNT(DISTINCT t.name) as team_count
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
                HAVING matches >= ? AND team_count >= ?
                ORDER BY matches DESC, team_count DESC
            """, (min_matches, min_teams))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def split_player_by_teams(self, player_name, min_team_matches=10):
        """Split a player into separate entities based on team activity"""
        team_analysis = self.analyzer.analyze_first_name_activity(player_name)
        
        # Filter teams with enough activity
        significant_teams = {
            team: analysis for team, analysis in team_analysis.items()
            if analysis['matches'] >= min_team_matches
        }
        
        if len(significant_teams) < 2:
            return []  # Not worth splitting
        
        split_suggestions = []
        for team_name, analysis in significant_teams.items():
            # Clean team name for new player name
            clean_team = team_name.replace('(', '').replace(')', '').replace(' ', '_')
            new_player_name = f"{player_name} ({clean_team})"
            
            split_suggestions.append({
                'original_name': player_name,
                'new_name': new_player_name,
                'team_name': team_name,
                'matches': analysis['matches'],
                'first_date': analysis['first_date'],
                'last_date': analysis['last_date'],
                'years': sorted(analysis['years'])
            })
        
        return split_suggestions
    
    def create_new_players(self, split_suggestions, dry_run=True):
        """Create new player entries in the database"""
        created_players = []
        
        print(f"{'🔍 DRY RUN - Would create' if dry_run else '👥 Creating'} {len(split_suggestions)} new players...")
        
        if not dry_run:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                for suggestion in split_suggestions:
                    # Check if player already exists
                    cursor.execute("SELECT id FROM players WHERE name = ?", (suggestion['new_name'],))
                    if cursor.fetchone():
                        print(f"   ⏭️  Player '{suggestion['new_name']}' already exists")
                        continue
                    
                    # Create new player
                    cursor.execute("INSERT INTO players (name) VALUES (?)", (suggestion['new_name'],))
                    new_player_id = cursor.lastrowid
                    
                    created_players.append({
                        'id': new_player_id,
                        'name': suggestion['new_name'],
                        'original_name': suggestion['original_name'],
                        'team_name': suggestion['team_name']
                    })
                    
                    print(f"   ✅ Created player '{suggestion['new_name']}' (ID: {new_player_id})")
                
                conn.commit()
        else:
            for suggestion in split_suggestions:
                print(f"   📝 Would create: '{suggestion['new_name']}' for {suggestion['team_name']}")
                print(f"      {suggestion['matches']} matches, {suggestion['years'][0]}-{suggestion['years'][-1]}")
                created_players.append({
                    'name': suggestion['new_name'],
                    'original_name': suggestion['original_name'],
                    'team_name': suggestion['team_name']
                })
        
        return created_players
    
    def update_sub_match_participants(self, original_player_name, team_splits, dry_run=True):
        """Update sub_match_participants to use new player IDs"""
        if dry_run:
            print(f"🔍 DRY RUN - Would update sub_match_participants for '{original_player_name}'")
            return
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Get original player ID
            cursor.execute("SELECT id FROM players WHERE name = ?", (original_player_name,))
            original_id = cursor.fetchone()[0]
            
            total_updated = 0
            
            for split in team_splits:
                team_name = split['team_name']
                new_player_name = split['name']
                
                # Get new player ID
                cursor.execute("SELECT id FROM players WHERE name = ?", (new_player_name,))
                result = cursor.fetchone()
                if not result:
                    print(f"   ❌ New player '{new_player_name}' not found")
                    continue
                    
                new_player_id = result[0]
                
                # Update sub_match_participants for this team
                cursor.execute("""
                    UPDATE sub_match_participants 
                    SET player_id = ?
                    WHERE player_id = ?
                    AND sub_match_id IN (
                        SELECT sm.id 
                        FROM sub_matches sm
                        JOIN matches m ON sm.match_id = m.id
                        JOIN teams t1 ON t1.id = m.team1_id
                        JOIN teams t2 ON t2.id = m.team2_id
                        JOIN sub_match_participants smp ON smp.sub_match_id = sm.id
                        WHERE (smp.team_number = 1 AND t1.name = ?) 
                           OR (smp.team_number = 2 AND t2.name = ?)
                        AND smp.player_id = ?
                    )
                """, (new_player_id, original_id, team_name, team_name, original_id))
                
                updated_count = cursor.rowcount
                total_updated += updated_count
                print(f"   ✅ Updated {updated_count} matches for {new_player_name} ({team_name})")
            
            conn.commit()
            print(f"   📊 Total updated: {total_updated} sub_match_participants")
    
    def process_all_problematic_names(self, dry_run=True, min_team_matches=10):
        """Process all problematic names and split them"""
        problematic = self.get_unmapped_problematic_names()
        
        print(f"🔍 Processing {len(problematic)} problematic first names...")
        print()
        
        all_splits = []
        total_new_players = 0
        
        for player in problematic:
            name = player['name']
            print(f"📊 Analyzing '{name}' ({player['matches']} matches, {player['team_count']} teams)")
            
            split_suggestions = self.split_player_by_teams(name, min_team_matches)
            
            if not split_suggestions:
                print(f"   ⏭️  Not worth splitting (insufficient team activity)")
                continue
            
            print(f"   💡 Suggested splits:")
            for suggestion in split_suggestions:
                print(f"     - '{suggestion['new_name']}': {suggestion['matches']} matches in {suggestion['team_name']}")
            
            # Create new players
            created_players = self.create_new_players(split_suggestions, dry_run)
            total_new_players += len(created_players)
            
            if not dry_run and created_players:
                # Update sub_match_participants
                self.update_sub_match_participants(name, created_players, dry_run)
            
            all_splits.extend(split_suggestions)
            print()
        
        print(f"📊 Summary:")
        print(f"   Problematic names processed: {len(problematic)}")
        print(f"   {'Would create' if dry_run else 'Created'}: {total_new_players} new players")
        print(f"   Total splits suggested: {len(all_splits)}")
        
        return all_splits

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 player_splitter.py <command> [args...]")
        print("")
        print("Commands:")
        print("  list [min_matches] [min_teams]     - List problematic names still unmapped")
        print("  analyze <name> [min_team_matches]  - Analyze specific name for splitting")
        print("  split-all [min_team_matches] [--force] - Split all problematic names")
        print("")
        print("Examples:")
        print("  python3 player_splitter.py list")
        print("  python3 player_splitter.py analyze Johan 10")
        print("  python3 player_splitter.py split-all 8 --force")
        return 1
    
    splitter = PlayerSplitter()
    command = sys.argv[1]
    
    if command == "list":
        min_matches = int(sys.argv[2]) if len(sys.argv) > 2 else 20
        min_teams = int(sys.argv[3]) if len(sys.argv) > 3 else 2
        
        problematic = splitter.get_unmapped_problematic_names(min_matches, min_teams)
        print(f"📋 {len(problematic)} problematic names still unmapped:")
        for player in problematic:
            print(f"   {player['name']}: {player['matches']} matches, {player['team_count']} teams")
    
    elif command == "analyze":
        if len(sys.argv) < 3:
            print("Usage: analyze <player_name> [min_team_matches]")
            return 1
        
        player_name = sys.argv[2]
        min_team_matches = int(sys.argv[3]) if len(sys.argv) > 3 else 10
        
        splits = splitter.split_player_by_teams(player_name, min_team_matches)
        if splits:
            print(f"💡 Suggested splits for '{player_name}':")
            for split in splits:
                print(f"   '{split['new_name']}': {split['matches']} matches in {split['team_name']}")
        else:
            print(f"❌ No splits suggested for '{player_name}'")
    
    elif command == "split-all":
        min_team_matches = 10
        force = False
        
        for arg in sys.argv[2:]:
            if arg == "--force":
                force = True
            elif arg.isdigit():
                min_team_matches = int(arg)
        
        splits = splitter.process_all_problematic_names(dry_run=not force, min_team_matches=min_team_matches)
        
        if not force:
            print(f"\\n💡 Use --force to actually create the {len(splits)} suggested player splits")
    
    else:
        print(f"Unknown command: {command}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())