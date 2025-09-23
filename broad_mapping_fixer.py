#!/usr/bin/env python3
"""
Broad Mapping Fixer
Identifies and fixes mappings where source players have multi-team activity 
that shouldn't be mapped to single-team target players

Created: 2025-09-21
"""
import sqlite3
import sys
from collections import defaultdict
from player_splitter import PlayerSplitter

class BroadMappingFixer:
    def __init__(self, db_path="goldenstat.db"):
        self.db_path = db_path
        self.splitter = PlayerSplitter(db_path)
    
    def get_problematic_mappings(self):
        """Find mappings where source has multi-team activity"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Get all confirmed mappings with team analysis
            cursor.execute("""
                SELECT 
                    pm.id as mapping_id,
                    pm.source_player_id,
                    pm.target_player_id,
                    ps.name as source_name,
                    pt.name as target_name,
                    pm.canonical_name,
                    pm.mapping_type
                FROM player_mappings pm
                JOIN players ps ON pm.source_player_id = ps.id
                JOIN players pt ON pm.target_player_id = pt.id
                WHERE pm.status = 'confirmed'
                ORDER BY pm.id
            """)
            
            mappings = [dict(row) for row in cursor.fetchall()]
            problematic = []
            
            for mapping in mappings:
                source_id = mapping['source_player_id']
                target_id = mapping['target_player_id']
                
                # Get team counts for source and target
                cursor.execute("""
                    SELECT COUNT(DISTINCT t.name) as team_count
                    FROM sub_match_participants smp
                    JOIN sub_matches sm ON smp.sub_match_id = sm.id
                    JOIN matches m ON sm.match_id = m.id
                    JOIN teams t ON t.id = CASE WHEN smp.team_number = 1 THEN m.team1_id ELSE m.team2_id END
                    WHERE smp.player_id = ?
                """, (source_id,))
                
                source_teams = cursor.fetchone()
                source_team_count = source_teams[0] if source_teams else 0
                
                cursor.execute("""
                    SELECT COUNT(DISTINCT t.name) as team_count
                    FROM sub_match_participants smp
                    JOIN sub_matches sm ON smp.sub_match_id = sm.id
                    JOIN matches m ON sm.match_id = m.id
                    JOIN teams t ON t.id = CASE WHEN smp.team_number = 1 THEN m.team1_id ELSE m.team2_id END
                    WHERE smp.player_id = ?
                """, (target_id,))
                
                target_teams = cursor.fetchone()
                target_team_count = target_teams[0] if target_teams else 0
                
                # Problematic if source has more teams than reasonable for target
                if source_team_count >= 3 or (source_team_count >= 2 and target_team_count >= 3):
                    mapping['source_team_count'] = source_team_count
                    mapping['target_team_count'] = target_team_count
                    problematic.append(mapping)
            
            return problematic
    
    def analyze_mapping_teams(self, mapping):
        """Get detailed team analysis for a mapping"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            source_id = mapping['source_player_id']
            target_id = mapping['target_player_id']
            
            # Get source teams
            cursor.execute("""
                SELECT 
                    t.name as team_name,
                    COUNT(DISTINCT smp.sub_match_id) as matches,
                    MIN(m.match_date) as first_match,
                    MAX(m.match_date) as last_match
                FROM sub_match_participants smp
                JOIN sub_matches sm ON smp.sub_match_id = sm.id
                JOIN matches m ON sm.match_id = m.id
                JOIN teams t ON t.id = CASE WHEN smp.team_number = 1 THEN m.team1_id ELSE m.team2_id END
                WHERE smp.player_id = ?
                GROUP BY t.name
                ORDER BY matches DESC
            """, (source_id,))
            
            source_teams = [dict(row) for row in cursor.fetchall()]
            
            # Get target teams  
            cursor.execute("""
                SELECT 
                    t.name as team_name,
                    COUNT(DISTINCT smp.sub_match_id) as matches,
                    MIN(m.match_date) as first_match,
                    MAX(m.match_date) as last_match
                FROM sub_match_participants smp
                JOIN sub_matches sm ON smp.sub_match_id = sm.id
                JOIN matches m ON sm.match_id = m.id
                JOIN teams t ON t.id = CASE WHEN smp.team_number = 1 THEN m.team1_id ELSE m.team2_id END
                WHERE smp.player_id = ?
                GROUP BY t.name
                ORDER BY matches DESC
            """, (target_id,))
            
            target_teams = [dict(row) for row in cursor.fetchall()]
            
            return source_teams, target_teams
    
    def reverse_mapping(self, mapping_id, dry_run=True):
        """Reverse a specific mapping"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Get mapping details
            cursor.execute("""
                SELECT 
                    pm.source_player_id,
                    pm.target_player_id,
                    ps.name as source_name,
                    pt.name as target_name
                FROM player_mappings pm
                JOIN players ps ON pm.source_player_id = ps.id
                JOIN players pt ON pm.target_player_id = pt.id
                WHERE pm.id = ?
            """, (mapping_id,))
            
            mapping_info = dict(cursor.fetchone())
            source_id = mapping_info['source_player_id']
            target_id = mapping_info['target_player_id']
            
            # Count affected records
            cursor.execute("SELECT COUNT(*) FROM sub_match_participants WHERE player_id = ?", (target_id,))
            affected_count = cursor.fetchone()[0]
            
            print(f"{'Would reverse' if dry_run else 'Reversing'} mapping {mapping_id}:")
            print(f"   {mapping_info['source_name']} → {mapping_info['target_name']}")
            print(f"   Affected records: {affected_count}")
            
            if not dry_run and affected_count > 0:
                # Move records back from target to source
                cursor.execute("""
                    UPDATE sub_match_participants 
                    SET player_id = ?
                    WHERE player_id = ?
                """, (source_id, target_id))
                
                updated_count = cursor.rowcount
                print(f"   ✅ Moved {updated_count} records back to source player")
                
                # Delete the mapping
                cursor.execute("DELETE FROM player_mappings WHERE id = ?", (mapping_id,))
                print(f"   ✅ Deleted mapping")
                
                conn.commit()
                return updated_count
            
            return affected_count if dry_run else 0
    
    def fix_problematic_mappings(self, dry_run=True):
        """Fix all problematic broad mappings"""
        problematic = self.get_problematic_mappings()
        
        if not problematic:
            print("✅ No problematic broad mappings found!")
            return 0
        
        print(f"🔍 Found {len(problematic)} problematic broad mappings:")
        print()
        
        total_fixed = 0
        mappings_to_split = []
        
        for mapping in problematic:
            print(f"❌ Mapping {mapping['mapping_id']}: {mapping['source_name']} → {mapping['target_name']}")
            print(f"   Source teams: {mapping['source_team_count']}, Target teams: {mapping['target_team_count']}")
            
            # Get detailed team analysis
            source_teams, target_teams = self.analyze_mapping_teams(mapping)
            
            print(f"   Source team breakdown:")
            for team in source_teams:
                print(f"     - {team['team_name']}: {team['matches']} matches")
            
            print(f"   Target team breakdown:")
            for team in target_teams:
                print(f"     - {team['team_name']}: {team['matches']} matches")
            
            # Reverse the mapping
            if not dry_run:
                reversed_count = self.reverse_mapping(mapping['mapping_id'], dry_run=False)
                total_fixed += 1
                
                # Add to split list if source has multiple teams
                if mapping['source_team_count'] >= 2:
                    mappings_to_split.append(mapping['source_name'])
            else:
                self.reverse_mapping(mapping['mapping_id'], dry_run=True)
                total_fixed += 1
                
                if mapping['source_team_count'] >= 2:
                    mappings_to_split.append(mapping['source_name'])
            
            print()
        
        print(f"📊 Summary:")
        print(f"   {'Would reverse' if dry_run else 'Reversed'}: {total_fixed} problematic mappings")
        print(f"   Players needing splits: {len(set(mappings_to_split))}")
        
        if mappings_to_split:
            print(f"   Players to split: {list(set(mappings_to_split))}")
        
        return total_fixed, list(set(mappings_to_split))
    
    def split_reversed_players(self, player_names, dry_run=True):
        """Split players that were reversed from broad mappings"""
        print(f"📊 {'Would split' if dry_run else 'Splitting'} {len(player_names)} reversed players...")
        
        total_new_players = 0
        
        for player_name in player_names:
            print(f"\n🔄 Processing {player_name}...")
            
            # Get split suggestions
            split_suggestions = self.splitter.split_player_by_teams(player_name, min_team_matches=10)
            
            if not split_suggestions:
                print(f"   ⏭️  No splits suggested for {player_name}")
                continue
            
            print(f"   💡 {len(split_suggestions)} splits suggested:")
            for suggestion in split_suggestions:
                print(f"     - {suggestion['new_name']}: {suggestion['matches']} matches in {suggestion['team_name']}")
            
            if not dry_run:
                # Create new players
                created_players = self.splitter.create_new_players(split_suggestions, dry_run=False)
                total_new_players += len(created_players)
                
                if created_players:
                    # Update sub_match_participants
                    self.splitter.update_sub_match_participants(player_name, created_players, dry_run=False)
            else:
                total_new_players += len(split_suggestions)
        
        print(f"\n📊 Split summary:")
        print(f"   {'Would create' if dry_run else 'Created'}: {total_new_players} new players")
        
        return total_new_players

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 broad_mapping_fixer.py <command> [args...]")
        print("")
        print("Commands:")
        print("  analyze                     - Analyze problematic broad mappings")
        print("  fix [--force]               - Fix all problematic mappings")
        print("  check <mapping_id>          - Check specific mapping")
        print("  full-fix [--force]          - Fix mappings and split players")
        print("")
        print("Examples:")
        print("  python3 broad_mapping_fixer.py analyze")
        print("  python3 broad_mapping_fixer.py fix --force")
        print("  python3 broad_mapping_fixer.py check 951")
        print("  python3 broad_mapping_fixer.py full-fix --force")
        return 1
    
    fixer = BroadMappingFixer()
    command = sys.argv[1]
    force = "--force" in sys.argv
    
    if command == "analyze":
        problematic = fixer.get_problematic_mappings()
        print(f"📋 Found {len(problematic)} problematic broad mappings:")
        
        for mapping in problematic:
            print(f"   ID {mapping['mapping_id']}: {mapping['source_name']} → {mapping['target_name']}")
            print(f"     Source teams: {mapping['source_team_count']}, Target teams: {mapping['target_team_count']}")
    
    elif command == "fix":
        fixed_count, to_split = fixer.fix_problematic_mappings(dry_run=not force)
        if not force:
            print(f"\n💡 Use --force to actually reverse {fixed_count} problematic mappings")
    
    elif command == "check":
        if len(sys.argv) < 3:
            print("Usage: check <mapping_id>")
            return 1
        mapping_id = int(sys.argv[2])
        
        # Find the mapping
        problematic = fixer.get_problematic_mappings()
        mapping = next((m for m in problematic if m['mapping_id'] == mapping_id), None)
        
        if not mapping:
            print(f"❌ Mapping {mapping_id} not found in problematic list")
            return 1
        
        print(f"🔍 Analyzing mapping {mapping_id}:")
        print(f"   {mapping['source_name']} → {mapping['target_name']}")
        
        source_teams, target_teams = fixer.analyze_mapping_teams(mapping)
        
        print(f"   Source teams ({len(source_teams)}):")
        for team in source_teams:
            print(f"     - {team['team_name']}: {team['matches']} matches")
        
        print(f"   Target teams ({len(target_teams)}):")
        for team in target_teams:
            print(f"     - {team['team_name']}: {team['matches']} matches")
    
    elif command == "full-fix":
        print("🚀 Running full broad mapping fix process...\n")
        
        # Step 1: Fix mappings
        print("Step 1: Reversing problematic mappings...")
        fixed_count, to_split = fixer.fix_problematic_mappings(dry_run=not force)
        print()
        
        # Step 2: Split players
        if to_split:
            print("Step 2: Splitting reversed players...")
            split_count = fixer.split_reversed_players(to_split, dry_run=not force)
            print()
        else:
            split_count = 0
            print("Step 2: No players need splitting")
        
        if force:
            print(f"🎉 Process complete!")
            print(f"   Reversed: {fixed_count} problematic mappings")
            print(f"   Created: {split_count} new split players")
        else:
            print(f"🔍 DRY RUN complete!")
            print(f"   Would reverse: {fixed_count} problematic mappings")
            print(f"   Would create: {split_count} new split players")
            print(f"\n💡 Use --force to actually execute the full process")
    
    else:
        print(f"Unknown command: {command}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())