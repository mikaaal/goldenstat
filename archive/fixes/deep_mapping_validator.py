#!/usr/bin/env python3
"""
Deep Mapping Validator
Performs detailed analysis of mappings by examining actual sub_matches

Created: 2025-09-21
"""
import sqlite3
import sys
from collections import defaultdict
from datetime import datetime

class DeepMappingValidator:
    def __init__(self, db_path="goldenstat.db"):
        self.db_path = db_path
    
    def get_player_detailed_activity(self, player_id):
        """Get detailed activity for a player including specific matches"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT 
                    sm.id as sub_match_id,
                    m.match_date,
                    t.name as team_name,
                    smp.team_number,
                    strftime('%Y-%m', m.match_date) as year_month,
                    strftime('%Y', m.match_date) as year
                FROM sub_match_participants smp
                JOIN sub_matches sm ON smp.sub_match_id = sm.id
                JOIN matches m ON sm.match_id = m.id
                JOIN teams t ON t.id = CASE WHEN smp.team_number = 1 THEN m.team1_id ELSE m.team2_id END
                WHERE smp.player_id = ?
                ORDER BY m.match_date
            """, (player_id,))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def analyze_team_similarity(self, team1, team2):
        """Analyze if two team names likely refer to the same club/team"""
        import re
        
        def normalize_team_name(name):
            # Remove division markers and clean up
            normalized = re.sub(r'\s*\([^)]*\)$', '', name)  # Remove (division) at end
            normalized = re.sub(r'\s*(SL\d+|Superligan|DS|1[A-F][A-E]?|2[A-F][A-E]?|3[A-F][A-E]?)$', '', normalized)
            # Clean up whitespace and special characters
            normalized = re.sub(r'\s+', ' ', normalized)  # Multiple spaces to single
            normalized = re.sub(r'[\xa0]', ' ', normalized)  # Non-breaking space to normal
            return normalized.strip()
        
        def extract_club_name(name):
            # Extract the core club name by removing common prefixes/suffixes
            core = normalize_team_name(name)
            # Remove common dart-related words that might differ
            core = re.sub(r'\s*(DC|Dart|Dartclub|Dartförening|Dart\s*Club)(\s|$)', '', core, flags=re.IGNORECASE)
            return core.strip()
        
        norm1 = normalize_team_name(team1)
        norm2 = normalize_team_name(team2)
        club1 = extract_club_name(team1)
        club2 = extract_club_name(team2)
        
        # Exact match after normalization
        if norm1 == norm2:
            return True, 1.0, "Same team, different divisions"
        
        # Club name match (allows for different divisions)
        if club1 and club2 and club1.lower() == club2.lower() and len(club1) >= 3:
            return True, 0.95, "Same club, different teams/divisions"
        
        # Check for common variations
        variations = [
            (norm1.replace(' ', ''), norm2.replace(' ', '')),  # Remove spaces
            (norm1.replace('ö', 'o'), norm2.replace('ö', 'o')),  # Replace Swedish chars
            (norm1.replace('ä', 'a'), norm2.replace('ä', 'a')),
            (norm1.replace('å', 'a'), norm2.replace('å', 'a')),
            (club1.replace(' ', ''), club2.replace(' ', '')),  # Club names without spaces
        ]
        
        for var1, var2 in variations:
            if var1 and var2 and var1.lower() == var2.lower() and len(var1) >= 3:
                return True, 0.9, "Same club, minor name variation"
        
        # Substring check (for abbreviations) - but only for longer names
        if len(norm1) >= 5 and len(norm2) >= 5:
            if norm1.lower() in norm2.lower() or norm2.lower() in norm1.lower():
                return True, 0.8, "Team name contains the other"
        
        # Check for club substring matches
        if len(club1) >= 4 and len(club2) >= 4:
            if club1.lower() in club2.lower() or club2.lower() in club1.lower():
                return True, 0.7, "Club name contains the other"
        
        # Special cases for known club variations
        special_cases = {
            'nacka wermdö': ['nacka', 'wermdö'],
            'stockholm bullseye': ['bullseye', 'stockholm'],
            'spikkastarna': ['spik', 'kastarna'],
            'dartanjang': ['darta', 'anjang'],
            'mitt i dc': ['mitt i'],
            'belkin power': ['belkin'],
        }
        
        for main_name, variations_list in special_cases.items():
            if any(var in norm1.lower() for var in variations_list) and any(var in norm2.lower() for var in variations_list):
                return True, 0.85, f"Known club variation ({main_name})"
        
        return False, 0.0, "Different clubs"
    
    def validate_mapping_deeply(self, mapping):
        """Perform deep validation of a mapping using sub_match data"""
        source_activity = self.get_player_detailed_activity(mapping['source_player_id'])
        target_activity = self.get_player_detailed_activity(mapping['target_player_id'])
        
        if not source_activity:
            return False, ["Source player has no match activity"], [], []
        
        if not target_activity:
            return False, ["Target player has no match activity"], [], []
        
        issues = []
        warnings = []
        
        # Analyze team patterns over time
        source_teams = set(act['team_name'] for act in source_activity)
        target_teams = set(act['team_name'] for act in target_activity)
        
        # Check if any teams are "the same" team (accounting for divisions)
        compatible_teams = []
        incompatible_source_teams = set(source_teams)
        incompatible_target_teams = set(target_teams)
        
        for s_team in source_teams:
            for t_team in target_teams:
                is_same, confidence, reason = self.analyze_team_similarity(s_team, t_team)
                if is_same and confidence >= 0.8:
                    compatible_teams.append(f"{s_team} ↔ {t_team} ({reason})")
                    incompatible_source_teams.discard(s_team)
                    incompatible_target_teams.discard(t_team)
        
        # CRITICAL: Check for completely incompatible teams
        # If source player has significant activity for teams that target never played for
        source_team_activity = defaultdict(int)
        target_team_activity = defaultdict(int)
        
        for act in source_activity:
            source_team_activity[act['team_name']] += 1
        
        for act in target_activity:
            target_team_activity[act['team_name']] += 1
        
        # Find source teams with significant activity (>5 matches) that are incompatible
        for s_team, match_count in source_team_activity.items():
            if match_count >= 5 and s_team in incompatible_source_teams:
                # Check if this team is completely incompatible with ALL target teams
                any_compatible = False
                for t_team in target_teams:
                    is_same, confidence, _ = self.analyze_team_similarity(s_team, t_team)
                    if is_same and confidence >= 0.5:  # Lower threshold for this check
                        any_compatible = True
                        break
                
                if not any_compatible:
                    issues.append(f"Source has significant activity ({match_count} matches) for incompatible team '{s_team}'")
        
        # Same check for target teams
        for t_team, match_count in target_team_activity.items():
            if match_count >= 5 and t_team in incompatible_target_teams:
                any_compatible = False
                for s_team in source_teams:
                    is_same, confidence, _ = self.analyze_team_similarity(s_team, t_team)
                    if is_same and confidence >= 0.5:
                        any_compatible = True
                        break
                
                if not any_compatible:
                    issues.append(f"Target has significant activity ({match_count} matches) for incompatible team '{t_team}'")
        
        # Group activities by year-month to check for overlaps
        source_monthly = defaultdict(list)
        target_monthly = defaultdict(list)
        
        for activity in source_activity:
            source_monthly[activity['year_month']].append(activity)
        
        for activity in target_activity:
            target_monthly[activity['year_month']].append(activity)
        
        # Check for temporal overlaps (same month activity)
        overlapping_months = set(source_monthly.keys()) & set(target_monthly.keys())
        
        if overlapping_months:
            for month in overlapping_months:
                source_teams_month = set(act['team_name'] for act in source_monthly[month])
                target_teams_month = set(act['team_name'] for act in target_monthly[month])
                
                # Check if teams are actually the same (accounting for divisions)
                teams_are_same = False
                for s_team in source_teams_month:
                    for t_team in target_teams_month:
                        is_same, confidence, reason = self.analyze_team_similarity(s_team, t_team)
                        if is_same and confidence >= 0.8:
                            teams_are_same = True
                            break
                    if teams_are_same:
                        break
                
                if not teams_are_same:
                    issues.append(f"Playing for different teams in {month}: {source_teams_month} vs {target_teams_month}")
        
        # Check if there are ANY compatible teams
        if not compatible_teams:
            issues.append(f"No compatible teams found: {source_teams} vs {target_teams}")
        
        # Check for reasonable temporal progression
        source_years = set(act['year'] for act in source_activity)
        target_years = set(act['year'] for act in target_activity)
        
        if not (source_years & target_years) and not compatible_teams:
            # No temporal overlap AND no team compatibility is suspicious
            min_source = min(source_years)
            max_source = max(source_years)
            min_target = min(target_years)
            max_target = max(target_years)
            
            gap = abs(int(max_source) - int(min_target)) if max_source < min_target else abs(int(max_target) - int(min_source))
            if gap > 1:  # More than 1 year gap
                issues.append(f"Large temporal gap with no team overlap: {min_source}-{max_source} vs {min_target}-{max_target}")
        
        # Additional insights
        insights = []
        if compatible_teams:
            insights.extend(compatible_teams)
        
        # Show team activity breakdown
        insights.append(f"Source teams: {dict(source_team_activity)}")
        insights.append(f"Target teams: {dict(target_team_activity)}")
        insights.append(f"Source active: {min(source_years)}-{max(source_years)} ({len(source_activity)} matches)")
        insights.append(f"Target active: {min(target_years)}-{max(target_years)} ({len(target_activity)} matches)")
        
        return len(issues) == 0, issues, warnings, insights
    
    def validate_specific_mapping(self, mapping_id):
        """Validate a specific mapping by ID"""
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
                    pt.name as target_name
                FROM player_mappings pm
                JOIN players ps ON pm.source_player_id = ps.id
                JOIN players pt ON pm.target_player_id = pt.id
                WHERE pm.id = ?
            """, (mapping_id,))
            
            result = cursor.fetchone()
            if not result:
                print(f"❌ Mapping ID {mapping_id} not found")
                return
            
            mapping = dict(result)
            
            print(f"🔍 Deep validation of mapping ID {mapping_id}:")
            print(f"   {mapping['source_name']} → {mapping['target_name']}")
            print(f"   Canonical: {mapping['canonical_name']}")
            print(f"   Type: {mapping['mapping_type']}, Confidence: {mapping['confidence']}%")
            print()
            
            is_valid, issues, warnings, insights = self.validate_mapping_deeply(mapping)
            
            if is_valid:
                print("   ✅ VALID mapping")
            else:
                print("   ❌ INVALID mapping")
                print("   Issues:")
                for issue in issues:
                    print(f"     - {issue}")
            
            if warnings:
                print("   ⚠️  Warnings:")
                for warning in warnings:
                    print(f"     - {warning}")
            
            print("   📊 Insights:")
            for insight in insights:
                print(f"     - {insight}")
    
    def batch_deep_validate(self, limit=None, show_valid=False):
        """Perform deep validation on all mappings"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            query = """
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
                WHERE pm.status = 'confirmed'
                ORDER BY pm.id
            """
            
            if limit:
                query += f" LIMIT {limit}"
            
            cursor.execute(query)
            mappings = [dict(row) for row in cursor.fetchall()]
        
        print(f"🔍 Deep validating {len(mappings)} mappings...")
        print()
        
        valid_count = 0
        invalid_count = 0
        invalid_mappings = []
        
        for i, mapping in enumerate(mappings, 1):
            if i % 50 == 0:
                print(f"   Progress: {i}/{len(mappings)} ({i/len(mappings)*100:.1f}%)")
            
            is_valid, issues, warnings, insights = self.validate_mapping_deeply(mapping)
            
            if is_valid:
                valid_count += 1
                if show_valid:
                    print(f"✅ ID {mapping['mapping_id']}: {mapping['source_name']} → {mapping['target_name']}")
            else:
                invalid_count += 1
                invalid_mappings.append({
                    'mapping': mapping,
                    'issues': issues,
                    'warnings': warnings,
                    'insights': insights
                })
                
                print(f"❌ ID {mapping['mapping_id']}: {mapping['source_name']} → {mapping['target_name']}")
                for issue in issues:
                    print(f"   - {issue}")
        
        print(f"\n📊 Deep Validation Summary:")
        print(f"   Total mappings: {len(mappings)}")
        print(f"   Valid mappings: {valid_count}")
        print(f"   Invalid mappings: {invalid_count}")
        print(f"   Accuracy: {valid_count/len(mappings)*100:.1f}%")
        
        return invalid_mappings

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 deep_mapping_validator.py <command> [args...]")
        print("")
        print("Commands:")
        print("  validate <mapping_id>       - Deep validate specific mapping")
        print("  batch [limit] [--show-valid] - Deep validate all mappings")
        print("")
        print("Examples:")
        print("  python3 deep_mapping_validator.py validate 89")
        print("  python3 deep_mapping_validator.py batch 50")
        print("  python3 deep_mapping_validator.py batch 100 --show-valid")
        return 1
    
    validator = DeepMappingValidator()
    command = sys.argv[1]
    
    if command == "validate":
        if len(sys.argv) < 3:
            print("Usage: validate <mapping_id>")
            return 1
        mapping_id = int(sys.argv[2])
        validator.validate_specific_mapping(mapping_id)
    
    elif command == "batch":
        limit = int(sys.argv[2]) if len(sys.argv) > 2 and sys.argv[2].isdigit() else None
        show_valid = "--show-valid" in sys.argv
        validator.batch_deep_validate(limit, show_valid)
    
    else:
        print(f"Unknown command: {command}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())