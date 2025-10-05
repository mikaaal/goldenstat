#!/usr/bin/env python3
"""
Comprehensive Mapping Verifier
Systematically verifies ALL mappings and player data for any type of inconsistency

Created: 2025-09-21
"""
import sqlite3
import sys
from datetime import datetime
from collections import defaultdict
from temporal_overlap_detector import TemporalOverlapDetector

class ComprehensiveMappingVerifier:
    def __init__(self, db_path="goldenstat.db"):
        self.db_path = db_path
        self.temporal_detector = TemporalOverlapDetector(db_path)
    
    def extract_club_name(self, team_name):
        """Extract club name from team name"""
        return self.temporal_detector.extract_club_name(team_name)
    
    def get_all_players_with_activity(self, min_matches=10):
        """Get all players with significant activity"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT 
                    p.id,
                    p.name,
                    COUNT(DISTINCT smp.sub_match_id) as total_matches,
                    COUNT(DISTINCT t.name) as team_count,
                    MIN(m.match_date) as first_match,
                    MAX(m.match_date) as last_match
                FROM players p
                JOIN sub_match_participants smp ON p.id = smp.player_id
                JOIN sub_matches sm ON smp.sub_match_id = sm.id
                JOIN matches m ON sm.match_id = m.id
                JOIN teams t ON t.id = CASE WHEN smp.team_number = 1 THEN m.team1_id ELSE m.team2_id END
                GROUP BY p.id, p.name
                HAVING total_matches >= ?
                ORDER BY total_matches DESC
            """, (min_matches,))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def get_player_club_activity(self, player_id):
        """Get detailed club activity for a player"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
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
            """, (player_id,))
            
            activities = []
            for row in cursor.fetchall():
                activity = dict(row)
                activity['club_name'] = self.extract_club_name(activity['team_name'])
                activities.append(activity)
            
            return activities
    
    def check_temporal_overlaps(self, player_name, activities):
        """Check for temporal overlaps between different clubs"""
        return self.temporal_detector.detect_temporal_overlaps(player_name, activities)
    
    def check_suspicious_high_activity(self, player_data, max_reasonable_matches=150):
        """Check for suspiciously high match activity"""
        if player_data['total_matches'] > max_reasonable_matches:
            return {
                'type': 'high_activity',
                'severity': 'high',
                'message': f"Player has {player_data['total_matches']} matches (>{max_reasonable_matches}), likely multiple people",
                'matches': player_data['total_matches']
            }
        return None
    
    def check_multi_club_activity(self, activities, min_club_matches=5):
        """Check for activity across multiple clubs"""
        club_activities = defaultdict(int)
        for activity in activities:
            club_activities[activity['club_name']] += activity['matches']
        
        significant_clubs = {club: matches for club, matches in club_activities.items() 
                           if matches >= min_club_matches}
        
        if len(significant_clubs) > 1:
            return {
                'type': 'multi_club',
                'severity': 'medium',
                'message': f"Player active in {len(significant_clubs)} clubs: {list(significant_clubs.keys())}",
                'clubs': significant_clubs
            }
        return None
    
    def check_name_patterns(self, player_name):
        """Check for problematic name patterns"""
        issues = []
        
        # Single name (potential aggregation)
        if ' ' not in player_name.strip() and len(player_name.strip()) > 2:
            issues.append({
                'type': 'single_name',
                'severity': 'medium',
                'message': f"Single name '{player_name}' may represent multiple people"
            })
        
        # Very short names
        if len(player_name.strip()) <= 2:
            issues.append({
                'type': 'short_name',
                'severity': 'low',
                'message': f"Very short name '{player_name}' is suspicious"
            })
        
        # Names with numbers or special characters (excluding Swedish chars)
        import re
        if re.search(r'[0-9]', player_name):
            issues.append({
                'type': 'name_with_numbers',
                'severity': 'low',
                'message': f"Name contains numbers: '{player_name}'"
            })
        
        return issues
    
    def check_mapping_inconsistencies(self, player_name):
        """Check for mapping-related inconsistencies"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            issues = []
            
            # Check if player is both source and target in different mappings
            cursor.execute("""
                SELECT 
                    'source' as role,
                    pm.target_player_id as other_player_id,
                    pt.name as other_player_name
                FROM player_mappings pm
                JOIN players ps ON pm.source_player_id = ps.id
                JOIN players pt ON pm.target_player_id = pt.id
                WHERE ps.name = ? AND pm.status = 'confirmed'
                
                UNION ALL
                
                SELECT 
                    'target' as role,
                    pm.source_player_id as other_player_id,
                    ps.name as other_player_name
                FROM player_mappings pm
                JOIN players ps ON pm.source_player_id = ps.id
                JOIN players pt ON pm.target_player_id = pt.id
                WHERE pt.name = ? AND pm.status = 'confirmed'
            """, (player_name, player_name))
            
            mappings = cursor.fetchall()
            
            # Check if player has no activity but is target of mappings
            cursor.execute("SELECT COUNT(*) FROM sub_match_participants smp JOIN players p ON smp.player_id = p.id WHERE p.name = ?", (player_name,))
            activity_count = cursor.fetchone()[0]
            
            target_mappings = [m for m in mappings if m['role'] == 'target']
            source_mappings = [m for m in mappings if m['role'] == 'source']
            
            if activity_count == 0 and target_mappings:
                issues.append({
                    'type': 'target_no_activity',
                    'severity': 'high',
                    'message': f"Player is target of {len(target_mappings)} mappings but has no match activity",
                    'mappings': len(target_mappings)
                })
            
            if activity_count > 0 and source_mappings:
                issues.append({
                    'type': 'source_with_activity',
                    'severity': 'high',
                    'message': f"Player is source of {len(source_mappings)} mappings but still has {activity_count} match activities",
                    'mappings': len(source_mappings),
                    'activities': activity_count
                })
            
            return issues
    
    def verify_single_player(self, player_data):
        """Comprehensive verification of a single player"""
        player_name = player_data['name']
        player_id = player_data['id']
        
        issues = []
        
        # Get detailed activity
        activities = self.get_player_club_activity(player_id)
        
        # Check various issue types
        high_activity_issue = self.check_suspicious_high_activity(player_data)
        if high_activity_issue:
            issues.append(high_activity_issue)
        
        multi_club_issue = self.check_multi_club_activity(activities)
        if multi_club_issue:
            issues.append(multi_club_issue)
        
        temporal_overlaps = self.check_temporal_overlaps(player_name, activities)
        if temporal_overlaps:
            issues.append({
                'type': 'temporal_overlap',
                'severity': 'high',
                'message': f"Player has {len(temporal_overlaps)} temporal overlaps between different clubs",
                'overlaps': temporal_overlaps
            })
        
        name_issues = self.check_name_patterns(player_name)
        issues.extend(name_issues)
        
        mapping_issues = self.check_mapping_inconsistencies(player_name)
        issues.extend(mapping_issues)
        
        return {
            'player': player_data,
            'activities': activities,
            'issues': issues,
            'severity_score': self.calculate_severity_score(issues)
        }
    
    def calculate_severity_score(self, issues):
        """Calculate overall severity score for a player"""
        severity_weights = {'high': 10, 'medium': 5, 'low': 1}
        return sum(severity_weights.get(issue['severity'], 0) for issue in issues)
    
    def verify_all_players(self, min_matches=10, limit=None):
        """Verify all players systematically"""
        players = self.get_all_players_with_activity(min_matches)
        
        if limit:
            players = players[:limit]
        
        print(f"🔍 Verifying {len(players)} players with {min_matches}+ matches...")
        
        problematic_players = []
        
        for i, player in enumerate(players, 1):
            if i % 100 == 0:
                print(f"   Progress: {i}/{len(players)} ({i/len(players)*100:.1f}%)")
            
            verification_result = self.verify_single_player(player)
            
            if verification_result['issues']:
                problematic_players.append(verification_result)
        
        # Sort by severity
        problematic_players.sort(key=lambda x: x['severity_score'], reverse=True)
        
        return problematic_players
    
    def generate_verification_report(self, problematic_players, limit=None):
        """Generate detailed verification report"""
        if limit:
            problematic_players = problematic_players[:limit]
        
        print(f"\n📋 COMPREHENSIVE MAPPING VERIFICATION REPORT")
        print("=" * 80)
        print(f"Found {len(problematic_players)} players with issues")
        
        # Summary by issue type
        issue_counts = defaultdict(int)
        severity_counts = defaultdict(int)
        
        for player_result in problematic_players:
            for issue in player_result['issues']:
                issue_counts[issue['type']] += 1
                severity_counts[issue['severity']] += 1
        
        print(f"\n📊 Issue Summary:")
        print(f"   High severity: {severity_counts['high']}")
        print(f"   Medium severity: {severity_counts['medium']}")
        print(f"   Low severity: {severity_counts['low']}")
        
        print(f"\n📈 Issue Types:")
        for issue_type, count in sorted(issue_counts.items(), key=lambda x: x[1], reverse=True):
            print(f"   {issue_type}: {count}")
        
        print(f"\n🔍 Detailed Issues:")
        print("=" * 80)
        
        for player_result in problematic_players:
            player = player_result['player']
            issues = player_result['issues']
            activities = player_result['activities']
            
            print(f"\n❌ {player['name']} (ID: {player['id']}) - Severity: {player_result['severity_score']}")
            print(f"   📊 {player['total_matches']} matches, {player['team_count']} teams")
            print(f"   📅 {player['first_match'][:10]} → {player['last_match'][:10]}")
            
            # Show club breakdown
            club_summary = defaultdict(int)
            for activity in activities:
                club_summary[activity['club_name']] += activity['matches']
            
            if len(club_summary) > 1:
                print(f"   🏢 Clubs: {dict(club_summary)}")
            
            # Show issues
            for issue in issues:
                severity_icon = "🚨" if issue['severity'] == 'high' else "⚠️" if issue['severity'] == 'medium' else "ℹ️"
                print(f"   {severity_icon} {issue['message']}")
                
                # Show additional details for specific issue types
                if issue['type'] == 'temporal_overlap' and 'overlaps' in issue:
                    for overlap in issue['overlaps'][:3]:  # Show first 3 overlaps
                        print(f"      → {overlap['club1']} vs {overlap['club2']}: {overlap['overlap_days']} days")
        
        return issue_counts, severity_counts
    
    def recommend_fixes(self, problematic_players, limit=10):
        """Recommend automated fixes for the most severe issues"""
        print(f"\n🔧 RECOMMENDED FIXES")
        print("=" * 80)
        
        high_priority = [p for p in problematic_players if p['severity_score'] >= 10][:limit]
        
        print(f"Showing fixes for top {len(high_priority)} high-priority issues:")
        
        for player_result in high_priority:
            player = player_result['player']
            issues = player_result['issues']
            
            print(f"\n🎯 {player['name']} (Severity: {player_result['severity_score']})")
            
            has_temporal = any(i['type'] == 'temporal_overlap' for i in issues)
            has_high_activity = any(i['type'] == 'high_activity' for i in issues)
            has_multi_club = any(i['type'] == 'multi_club' for i in issues)
            
            if has_temporal:
                print(f"   💡 Fix: Use temporal_overlap_fixer.py fix '{player['name']}' --force")
            elif has_high_activity and has_multi_club:
                print(f"   💡 Fix: Manual review needed - likely represents multiple people")
                print(f"   💡 Consider: player_splitter.py analyze '{player['name']}'")
            elif any(i['type'] == 'source_with_activity' for i in issues):
                print(f"   💡 Fix: mapping_applier.py apply --force (mapping not applied)")
            elif any(i['type'] == 'single_name' for i in issues):
                print(f"   💡 Fix: first_name_analyzer.py suggest '{player['name']}'")
        
        return high_priority

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 comprehensive_mapping_verifier.py <command> [args...]")
        print("")
        print("Commands:")
        print("  verify-all [min_matches] [limit]    - Verify all players")
        print("  verify <player_name>                - Verify specific player")
        print("  report [limit]                      - Generate verification report")
        print("  fixes [limit]                       - Show recommended fixes")
        print("  full-report [min_matches]           - Full verification and report")
        print("")
        print("Examples:")
        print("  python3 comprehensive_mapping_verifier.py full-report 20")
        print("  python3 comprehensive_mapping_verifier.py verify 'Peter Söron'")
        print("  python3 comprehensive_mapping_verifier.py report 50")
        return 1
    
    verifier = ComprehensiveMappingVerifier()
    command = sys.argv[1]
    
    if command == "verify":
        if len(sys.argv) < 3:
            print("Usage: verify <player_name>")
            return 1
        
        player_name = sys.argv[2]
        
        # Find player
        with sqlite3.connect(verifier.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, name FROM players WHERE name = ?", (player_name,))
            result = cursor.fetchone()
            
            if not result:
                print(f"❌ Player '{player_name}' not found")
                return 1
            
            player_data = {'id': result[0], 'name': result[1]}
        
        # Get full player data
        players = verifier.get_all_players_with_activity(1)
        player_data = next((p for p in players if p['name'] == player_name), None)
        
        if not player_data:
            print(f"❌ Player '{player_name}' has no match activity")
            return 1
        
        result = verifier.verify_single_player(player_data)
        
        print(f"🔍 Verification for '{player_name}':")
        print(f"   Matches: {player_data['total_matches']}")
        print(f"   Teams: {player_data['team_count']}")
        print(f"   Period: {player_data['first_match'][:10]} → {player_data['last_match'][:10]}")
        
        if result['issues']:
            print(f"   Issues found: {len(result['issues'])}")
            for issue in result['issues']:
                severity_icon = "🚨" if issue['severity'] == 'high' else "⚠️" if issue['severity'] == 'medium' else "ℹ️"
                print(f"   {severity_icon} {issue['message']}")
        else:
            print("   ✅ No issues found")
    
    elif command == "verify-all":
        min_matches = int(sys.argv[2]) if len(sys.argv) > 2 else 20
        limit = int(sys.argv[3]) if len(sys.argv) > 3 else None
        
        problematic = verifier.verify_all_players(min_matches, limit)
        print(f"\n✅ Verification complete: {len(problematic)} players with issues found")
    
    elif command == "report":
        limit = int(sys.argv[2]) if len(sys.argv) > 2 else 50
        
        # First verify all players
        problematic = verifier.verify_all_players(20)
        verifier.generate_verification_report(problematic, limit)
    
    elif command == "fixes":
        limit = int(sys.argv[2]) if len(sys.argv) > 2 else 20
        
        # First verify all players
        problematic = verifier.verify_all_players(20)
        verifier.recommend_fixes(problematic, limit)
    
    elif command == "full-report":
        min_matches = int(sys.argv[2]) if len(sys.argv) > 2 else 20
        
        print("🚀 Running comprehensive mapping verification...")
        problematic = verifier.verify_all_players(min_matches)
        verifier.generate_verification_report(problematic, 50)
        verifier.recommend_fixes(problematic, 20)
    
    else:
        print(f"Unknown command: {command}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())