#!/usr/bin/env python3
"""
Mapping Validator
Validates all player mappings to ensure they are logically correct

Created: 2025-09-21
"""
import sqlite3
import sys
from collections import defaultdict

class MappingValidator:
    def __init__(self, db_path="goldenstat.db"):
        self.db_path = db_path
    
    def get_all_mappings(self, status='confirmed'):
        """Get all mappings with player details"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT 
                    pm.id as mapping_id,
                    pm.source_player_id,
                    pm.target_player_id,
                    pm.canonical_name,
                    pm.mapping_type,
                    pm.confidence,
                    ps.name as source_name,
                    pt.name as target_name,
                    pm.created_at
                FROM player_mappings pm
                JOIN players ps ON pm.source_player_id = ps.id
                JOIN players pt ON pm.target_player_id = pt.id
                WHERE pm.status = ?
                ORDER BY pm.canonical_name, pm.created_at
            """, (status,))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def get_player_teams(self, player_id):
        """Get all teams for a specific player ID"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT DISTINCT 
                    t.name as team_name,
                    COUNT(DISTINCT smp.sub_match_id) as matches,
                    MIN(m.match_date) as first_match,
                    MAX(m.match_date) as last_match,
                    strftime('%Y', MIN(m.match_date)) as first_year,
                    strftime('%Y', MAX(m.match_date)) as last_year
                FROM sub_match_participants smp
                JOIN sub_matches sm ON smp.sub_match_id = sm.id
                JOIN matches m ON sm.match_id = m.id
                JOIN teams t ON t.id = CASE WHEN smp.team_number = 1 THEN m.team1_id ELSE m.team2_id END
                WHERE smp.player_id = ?
                GROUP BY t.name
                ORDER BY matches DESC
            """, (player_id,))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def validate_mapping(self, mapping):
        """Validate a single mapping"""
        issues = []
        
        # Get team data for both players
        source_teams = self.get_player_teams(mapping['source_player_id'])
        target_teams = self.get_player_teams(mapping['target_player_id'])
        
        if not source_teams:
            issues.append("Source player has no match data")
        
        if not target_teams:
            issues.append("Target player has no match data")
            
        if not source_teams or not target_teams:
            return issues
        
        # Extract team names for comparison
        source_team_names = set(team['team_name'] for team in source_teams)
        target_team_names = set(team['team_name'] for team in target_teams)
        
        # Check for team overlap
        common_teams = source_team_names.intersection(target_team_names)
        
        if not common_teams:
            issues.append(f"No common teams (Source: {source_team_names}, Target: {target_team_names})")
        
        # Check for temporal overlap
        source_years = set()
        target_years = set()
        
        for team in source_teams:
            start_year = int(team['first_year'])
            end_year = int(team['last_year'])
            source_years.update(range(start_year, end_year + 1))
        
        for team in target_teams:
            start_year = int(team['first_year'])
            end_year = int(team['last_year'])
            target_years.update(range(start_year, end_year + 1))
        
        common_years = source_years.intersection(target_years)
        if not common_years:
            issues.append(f"No temporal overlap (Source: {min(source_years)}-{max(source_years)}, Target: {min(target_years)}-{max(target_years)})")
        
        # Check for suspicious simultaneous activity
        for year in common_years:
            source_teams_in_year = [team for team in source_teams 
                                  if int(team['first_year']) <= year <= int(team['last_year'])]
            target_teams_in_year = [team for team in target_teams 
                                  if int(team['first_year']) <= year <= int(team['last_year'])]
            
            if len(source_teams_in_year) > 0 and len(target_teams_in_year) > 0:
                source_team_names_year = set(team['team_name'] for team in source_teams_in_year)
                target_team_names_year = set(team['team_name'] for team in target_teams_in_year)
                
                if not source_team_names_year.intersection(target_team_names_year):
                    issues.append(f"Different teams in {year}: {source_team_names_year} vs {target_team_names_year}")
        
        return issues
    
    def validate_all_mappings(self, show_details=False):
        """Validate all confirmed mappings"""
        mappings = self.get_all_mappings('confirmed')
        
        print(f"🔍 Validating {len(mappings)} confirmed mappings...")
        print()
        
        problematic_mappings = []
        
        for i, mapping in enumerate(mappings, 1):
            issues = self.validate_mapping(mapping)
            
            if issues:
                problematic_mappings.append({
                    'mapping': mapping,
                    'issues': issues
                })
                
                print(f"⚠️  Mapping {i}: {mapping['source_name']} → {mapping['target_name']}")
                print(f"   ID: {mapping['mapping_id']}, Type: {mapping['mapping_type']}")
                for issue in issues:
                    print(f"   ❌ {issue}")
                
                if show_details:
                    source_teams = self.get_player_teams(mapping['source_player_id'])
                    target_teams = self.get_player_teams(mapping['target_player_id'])
                    
                    print(f"   Source teams:")
                    for team in source_teams:
                        print(f"     - {team['team_name']}: {team['matches']} matches ({team['first_year']}-{team['last_year']})")
                    
                    print(f"   Target teams:")
                    for team in target_teams:
                        print(f"     - {team['team_name']}: {team['matches']} matches ({team['first_year']}-{team['last_year']})")
                
                print()
        
        print(f"📊 Validation Summary:")
        print(f"   Total mappings: {len(mappings)}")
        print(f"   Problematic mappings: {len(problematic_mappings)}")
        print(f"   Valid mappings: {len(mappings) - len(problematic_mappings)}")
        
        return problematic_mappings
    
    def check_specific_player(self, player_name):
        """Check all mappings involving a specific player"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Find mappings where this player is involved
            cursor.execute("""
                SELECT 
                    pm.id as mapping_id,
                    pm.source_player_id,
                    pm.target_player_id,
                    pm.canonical_name,
                    pm.mapping_type,
                    pm.confidence,
                    ps.name as source_name,
                    pt.name as target_name
                FROM player_mappings pm
                JOIN players ps ON pm.source_player_id = ps.id
                JOIN players pt ON pm.target_player_id = pt.id
                WHERE ps.name LIKE ? OR pt.name LIKE ? OR pm.canonical_name LIKE ?
                ORDER BY pm.id
            """, (f"%{player_name}%", f"%{player_name}%", f"%{player_name}%"))
            
            mappings = [dict(row) for row in cursor.fetchall()]
            
            if not mappings:
                print(f"📭 No mappings found for '{player_name}'")
                return
            
            print(f"🔍 Found {len(mappings)} mapping(s) for '{player_name}':")
            print()
            
            for mapping in mappings:
                print(f"📝 Mapping ID {mapping['mapping_id']}:")
                print(f"   {mapping['source_name']} → {mapping['target_name']}")
                print(f"   Canonical: {mapping['canonical_name']}")
                print(f"   Type: {mapping['mapping_type']}, Confidence: {mapping['confidence']}%")
                
                issues = self.validate_mapping(mapping)
                if issues:
                    print(f"   ⚠️  Issues found:")
                    for issue in issues:
                        print(f"     - {issue}")
                else:
                    print(f"   ✅ Validation passed")
                
                # Show team details
                source_teams = self.get_player_teams(mapping['source_player_id'])
                target_teams = self.get_player_teams(mapping['target_player_id'])
                
                print(f"   Source teams ({mapping['source_name']}):")
                for team in source_teams:
                    print(f"     - {team['team_name']}: {team['matches']} matches ({team['first_year']}-{team['last_year']})")
                
                print(f"   Target teams ({mapping['target_name']}):")
                for team in target_teams:
                    print(f"     - {team['team_name']}: {team['matches']} matches ({team['first_year']}-{team['last_year']})")
                
                print()

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 mapping_validator.py <command> [args...]")
        print("")
        print("Commands:")
        print("  validate [--details]        - Validate all confirmed mappings")
        print("  check <player_name>         - Check specific player mappings")
        print("")
        print("Examples:")
        print("  python3 mapping_validator.py validate")
        print("  python3 mapping_validator.py validate --details")
        print("  python3 mapping_validator.py check 'Mikael Wetter'")
        return 1
    
    validator = MappingValidator()
    command = sys.argv[1]
    
    if command == "validate":
        show_details = "--details" in sys.argv
        validator.validate_all_mappings(show_details)
    
    elif command == "check":
        if len(sys.argv) < 3:
            print("Usage: check <player_name>")
            return 1
        player_name = sys.argv[2]
        validator.check_specific_player(player_name)
    
    else:
        print(f"Unknown command: {command}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())