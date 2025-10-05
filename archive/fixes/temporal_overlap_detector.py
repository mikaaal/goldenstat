#!/usr/bin/env python3
"""
Temporal Overlap Detector
Finds players who appear to play for different clubs during overlapping time periods
which indicates incorrect mappings

Created: 2025-09-21
"""
import sqlite3
import sys
from datetime import datetime
from collections import defaultdict

class TemporalOverlapDetector:
    def __init__(self, db_path="goldenstat.db"):
        self.db_path = db_path
    
    def extract_club_name(self, team_name):
        """Extract club name from team name by removing division markers"""
        # Remove common division markers
        markers = ['(1A)', '(1B)', '(1C)', '(1D)', '(1E)', '(1F)', '(1FA)', '(1FB)', '(1FC)', '(1FD)', '(1FE)', '(1FF)',
                  '(2A)', '(2B)', '(2C)', '(2D)', '(2E)', '(2F)', '(2FA)', '(2FB)', '(2FC)', '(2FD)', '(2FE)', '(2FF)',
                  '(3A)', '(3B)', '(3C)', '(3D)', '(3E)', '(3F)', '(3FA)', '(3FB)', '(3FC)', '(3FD)', '(3FE)', '(3FF)',
                  '(4A)', '(4B)', '(4C)', '(4D)', '(4E)', '(4F)', '(4FA)', '(4FB)', '(4FC)', '(4FD)', '(4FE)', '(4FF)',
                  '(SL1)', '(SL2)', '(SL3)', '(SL4)', '(SL5)', '(SL6)', '(SL7)', '(SL8)', '(SL9)', '(SL10)',
                  '(Superligan)', '(Division 1)', '(Division 2)', '(Division 3)', '(Division 4)',
                  ' SL1', ' SL2', ' SL3', ' SL4', ' SL5', ' SL6', ' SL7', ' SL8', ' SL9', ' SL10']
        
        club_name = team_name.strip()
        for marker in markers:
            club_name = club_name.replace(marker, '').strip()
        
        return club_name
    
    def get_player_activity_timeline(self, player_name, min_matches=20):
        """Get detailed timeline of player activity by team"""
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
                JOIN players p ON smp.player_id = p.id
                WHERE p.name = ?
                GROUP BY t.name
                HAVING matches >= ?
                ORDER BY first_match
            """, (player_name, min_matches))
            
            activities = []
            for row in cursor.fetchall():
                activity = dict(row)
                activity['club_name'] = self.extract_club_name(activity['team_name'])
                activities.append(activity)
            
            return activities
    
    def detect_temporal_overlaps(self, player_name, activities, overlap_days=7):
        """Detect if player has overlapping periods with different clubs"""
        overlaps = []
        
        # Group activities by club
        club_activities = defaultdict(list)
        for activity in activities:
            club_activities[activity['club_name']].append(activity)
        
        # Merge periods within same club
        merged_club_periods = {}
        for club, club_acts in club_activities.items():
            if len(club_acts) == 1:
                merged_club_periods[club] = [(club_acts[0]['first_match'], club_acts[0]['last_match'])]
            else:
                # Sort by start date and merge overlapping periods
                club_acts.sort(key=lambda x: x['first_match'])
                periods = []
                current_start = club_acts[0]['first_match']
                current_end = club_acts[0]['last_match']
                
                for act in club_acts[1:]:
                    if act['first_match'] <= current_end:  # Overlapping or adjacent
                        current_end = max(current_end, act['last_match'])
                    else:
                        periods.append((current_start, current_end))
                        current_start = act['first_match']
                        current_end = act['last_match']
                
                periods.append((current_start, current_end))
                merged_club_periods[club] = periods
        
        # Check for overlaps between different clubs
        clubs = list(merged_club_periods.keys())
        for i in range(len(clubs)):
            for j in range(i + 1, len(clubs)):
                club1, club2 = clubs[i], clubs[j]
                
                for period1 in merged_club_periods[club1]:
                    for period2 in merged_club_periods[club2]:
                        start1, end1 = period1
                        start2, end2 = period2
                        
                        # Check if periods overlap
                        overlap_start = max(start1, start2)
                        overlap_end = min(end1, end2)
                        
                        if overlap_start <= overlap_end:
                            # Calculate overlap duration
                            start_dt = datetime.fromisoformat(overlap_start.replace(' ', 'T'))
                            end_dt = datetime.fromisoformat(overlap_end.replace(' ', 'T'))
                            overlap_duration = (end_dt - start_dt).days
                            
                            if overlap_duration >= overlap_days:
                                overlaps.append({
                                    'player': player_name,
                                    'club1': club1,
                                    'club2': club2,
                                    'period1': period1,
                                    'period2': period2,
                                    'overlap_start': overlap_start,
                                    'overlap_end': overlap_end,
                                    'overlap_days': overlap_duration
                                })
        
        return overlaps
    
    def find_all_problematic_players(self, min_matches=20, min_teams=2):
        """Find all players with potential temporal overlaps"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Get players with activity in multiple teams
            cursor.execute("""
                SELECT 
                    p.name,
                    COUNT(DISTINCT smp.sub_match_id) as total_matches,
                    COUNT(DISTINCT t.name) as team_count
                FROM players p
                JOIN sub_match_participants smp ON p.id = smp.player_id
                JOIN sub_matches sm ON smp.sub_match_id = sm.id
                JOIN matches m ON sm.match_id = m.id
                JOIN teams t ON t.id = CASE WHEN smp.team_number = 1 THEN m.team1_id ELSE m.team2_id END
                GROUP BY p.id, p.name
                HAVING total_matches >= ? AND team_count >= ?
                ORDER BY total_matches DESC
            """, (min_matches, min_teams))
            
            candidates = [dict(row) for row in cursor.fetchall()]
            
        print(f"🔍 Analyzing {len(candidates)} players with {min_matches}+ matches and {min_teams}+ teams...")
        
        problematic_players = []
        
        for i, candidate in enumerate(candidates, 1):
            if i % 50 == 0:
                print(f"   Progress: {i}/{len(candidates)} ({i/len(candidates)*100:.1f}%)")
            
            player_name = candidate['name']
            activities = self.get_player_activity_timeline(player_name, min_matches=5)
            
            # Skip if only one club (extract unique clubs)
            unique_clubs = set(self.extract_club_name(act['team_name']) for act in activities)
            if len(unique_clubs) < 2:
                continue
            
            overlaps = self.detect_temporal_overlaps(player_name, activities)
            
            if overlaps:
                problematic_players.append({
                    'player': player_name,
                    'total_matches': candidate['total_matches'],
                    'team_count': candidate['team_count'],
                    'activities': activities,
                    'overlaps': overlaps
                })
        
        return problematic_players
    
    def report_problematic_players(self, problematic_players, limit=None):
        """Generate detailed report of problematic players"""
        if limit:
            problematic_players = problematic_players[:limit]
        
        print(f"\n📋 Found {len(problematic_players)} players with temporal overlaps:")
        print("=" * 80)
        
        for player_data in problematic_players:
            player = player_data['player']
            print(f"\n❌ {player} ({player_data['total_matches']} matches, {player_data['team_count']} teams)")
            
            print(f"   Timeline:")
            for activity in player_data['activities']:
                club = self.extract_club_name(activity['team_name'])
                print(f"     - {activity['team_name']} [{club}]: {activity['matches']} matches")
                print(f"       {activity['first_match'][:10]} → {activity['last_match'][:10]}")
            
            print(f"   ⚠️  Overlapping periods:")
            for overlap in player_data['overlaps']:
                print(f"     - {overlap['club1']} vs {overlap['club2']}")
                print(f"       Overlap: {overlap['overlap_start'][:10]} → {overlap['overlap_end'][:10]} ({overlap['overlap_days']} days)")
            
            print()

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 temporal_overlap_detector.py <command> [args...]")
        print("")
        print("Commands:")
        print("  analyze <player_name>              - Analyze specific player for overlaps")
        print("  find-all [min_matches] [min_teams] - Find all problematic players")
        print("  report [limit]                     - Generate report of problematic players")
        print("")
        print("Examples:")
        print("  python3 temporal_overlap_detector.py analyze 'Mikael Berg'")
        print("  python3 temporal_overlap_detector.py find-all 30 2")
        print("  python3 temporal_overlap_detector.py report 10")
        return 1
    
    detector = TemporalOverlapDetector()
    command = sys.argv[1]
    
    if command == "analyze":
        if len(sys.argv) < 3:
            print("Usage: analyze <player_name>")
            return 1
        
        player_name = sys.argv[2]
        activities = detector.get_player_activity_timeline(player_name, min_matches=5)
        
        if not activities:
            print(f"❌ No significant activity found for '{player_name}'")
            return 1
        
        print(f"🔍 Analyzing '{player_name}'...")
        overlaps = detector.detect_temporal_overlaps(player_name, activities)
        
        print(f"   Timeline:")
        for activity in activities:
            club = detector.extract_club_name(activity['team_name'])
            print(f"     - {activity['team_name']} [{club}]: {activity['matches']} matches")
            print(f"       {activity['first_match'][:10]} → {activity['last_match'][:10]}")
        
        if overlaps:
            print(f"\n   ❌ Found {len(overlaps)} temporal overlaps:")
            for overlap in overlaps:
                print(f"     - {overlap['club1']} vs {overlap['club2']}")
                print(f"       Overlap: {overlap['overlap_start'][:10]} → {overlap['overlap_end'][:10]} ({overlap['overlap_days']} days)")
        else:
            print(f"\n   ✅ No temporal overlaps found")
    
    elif command == "find-all":
        min_matches = int(sys.argv[2]) if len(sys.argv) > 2 else 30
        min_teams = int(sys.argv[3]) if len(sys.argv) > 3 else 2
        
        problematic = detector.find_all_problematic_players(min_matches, min_teams)
        print(f"\n✅ Found {len(problematic)} players with temporal overlaps")
        
        if problematic:
            print(f"\nTop 5 most problematic:")
            for player_data in problematic[:5]:
                overlap_count = len(player_data['overlaps'])
                print(f"   - {player_data['player']}: {player_data['total_matches']} matches, {overlap_count} overlaps")
    
    elif command == "report":
        limit = int(sys.argv[2]) if len(sys.argv) > 2 else None
        
        # First find problematic players
        problematic = detector.find_all_problematic_players(30, 2)
        detector.report_problematic_players(problematic, limit)
    
    else:
        print(f"Unknown command: {command}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())