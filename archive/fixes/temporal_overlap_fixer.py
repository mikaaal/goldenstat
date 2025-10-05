#!/usr/bin/env python3
"""
Temporal Overlap Fixer
Automatically fixes players who have temporal overlaps by splitting them into separate entities
based on club membership and temporal activity

Created: 2025-09-21
"""
import sqlite3
import sys
from datetime import datetime, timedelta
from collections import defaultdict
from temporal_overlap_detector import TemporalOverlapDetector

class TemporalOverlapFixer:
    def __init__(self, db_path="goldenstat.db"):
        self.db_path = db_path
        self.detector = TemporalOverlapDetector(db_path)
    
    def analyze_player_for_splitting(self, player_name):
        """Analyze how a player should be split based on temporal and club patterns"""
        activities = self.detector.get_player_activity_timeline(player_name, min_matches=5)
        overlaps = self.detector.detect_temporal_overlaps(player_name, activities)
        
        if not overlaps:
            return None
        
        # Group activities by club
        club_activities = defaultdict(list)
        for activity in activities:
            club_name = self.detector.extract_club_name(activity['team_name'])
            club_activities[club_name].append(activity)
        
        # For each club, determine the optimal time periods to avoid overlaps
        split_suggestions = []
        
        for club_name, club_acts in club_activities.items():
            # Merge overlapping periods within same club
            club_acts.sort(key=lambda x: x['first_match'])
            merged_periods = []
            
            if len(club_acts) == 1:
                merged_periods.append({
                    'club': club_name,
                    'teams': [club_acts[0]['team_name']],
                    'start': club_acts[0]['first_match'],
                    'end': club_acts[0]['last_match'],
                    'total_matches': club_acts[0]['matches']
                })
            else:
                # Merge periods that are close together (within 30 days)
                current_period = {
                    'club': club_name,
                    'teams': [club_acts[0]['team_name']],
                    'start': club_acts[0]['first_match'],
                    'end': club_acts[0]['last_match'],
                    'total_matches': club_acts[0]['matches']
                }
                
                for act in club_acts[1:]:
                    # Check if this activity is within 30 days of current period end
                    time_gap = (datetime.fromisoformat(act['first_match'].replace(' ', 'T')) - 
                              datetime.fromisoformat(current_period['end'].replace(' ', 'T'))).days
                    
                    if time_gap <= 30:  # Merge periods
                        current_period['teams'].append(act['team_name'])
                        current_period['end'] = max(current_period['end'], act['last_match'])
                        current_period['total_matches'] += act['matches']
                    else:  # Start new period
                        merged_periods.append(current_period)
                        current_period = {
                            'club': club_name,
                            'teams': [act['team_name']],
                            'start': act['first_match'],
                            'end': act['last_match'],
                            'total_matches': act['matches']
                        }
                
                merged_periods.append(current_period)
            
            split_suggestions.extend(merged_periods)
        
        # Sort by start date
        split_suggestions.sort(key=lambda x: x['start'])
        
        # Generate new player names
        for i, suggestion in enumerate(split_suggestions):
            club_clean = suggestion['club'].replace(' ', '_').replace('(', '').replace(')', '')
            
            if len(split_suggestions) == 1:
                # Only one period, just use club name
                suggestion['new_name'] = f"{player_name} ({club_clean})"
            else:
                # Multiple periods, add year to distinguish
                start_year = suggestion['start'][:4]
                suggestion['new_name'] = f"{player_name} ({club_clean}_{start_year})"
        
        return {
            'original_name': player_name,
            'overlaps': overlaps,
            'split_suggestions': split_suggestions
        }
    
    def create_split_players(self, split_analysis, dry_run=True):
        """Create new player entities for the split"""
        if not split_analysis or len(split_analysis['split_suggestions']) <= 1:
            return []
        
        original_name = split_analysis['original_name']
        suggestions = split_analysis['split_suggestions']
        
        print(f"{'🔍 DRY RUN - Would create' if dry_run else '👥 Creating'} {len(suggestions)} split players for '{original_name}':")
        
        created_players = []
        
        if not dry_run:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                for suggestion in suggestions:
                    new_name = suggestion['new_name']
                    
                    # Check if player already exists
                    cursor.execute("SELECT id FROM players WHERE name = ?", (new_name,))
                    if cursor.fetchone():
                        print(f"   ⏭️  Player '{new_name}' already exists")
                        continue
                    
                    # Create new player
                    cursor.execute("INSERT INTO players (name) VALUES (?)", (new_name,))
                    new_player_id = cursor.lastrowid
                    
                    created_players.append({
                        'id': new_player_id,
                        'name': new_name,
                        'original_name': original_name,
                        'club': suggestion['club'],
                        'start_date': suggestion['start'],
                        'end_date': suggestion['end'],
                        'teams': suggestion['teams'],
                        'total_matches': suggestion['total_matches']
                    })
                    
                    print(f"   ✅ Created '{new_name}' (ID: {new_player_id})")
                    print(f"      Period: {suggestion['start'][:10]} → {suggestion['end'][:10]}")
                    print(f"      Teams: {', '.join(suggestion['teams'])}")
                
                conn.commit()
        else:
            for suggestion in suggestions:
                created_players.append({
                    'name': suggestion['new_name'],
                    'original_name': original_name,
                    'club': suggestion['club'],
                    'start_date': suggestion['start'],
                    'end_date': suggestion['end'],
                    'teams': suggestion['teams'],
                    'total_matches': suggestion['total_matches']
                })
                
                print(f"   📝 Would create: '{suggestion['new_name']}'")
                print(f"      Period: {suggestion['start'][:10]} → {suggestion['end'][:10]}")
                print(f"      Teams: {', '.join(suggestion['teams'])}")
                print(f"      Matches: {suggestion['total_matches']}")
        
        return created_players
    
    def update_sub_match_participants_temporal(self, original_name, split_players, dry_run=True):
        """Update sub_match_participants based on temporal periods"""
        if dry_run:
            print(f"🔍 DRY RUN - Would update sub_match_participants for '{original_name}'")
            return
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Get original player ID
            cursor.execute("SELECT id FROM players WHERE name = ?", (original_name,))
            result = cursor.fetchone()
            if not result:
                print(f"   ❌ Original player '{original_name}' not found")
                return
            
            original_id = result[0]
            total_updated = 0
            
            for split in split_players:
                new_player_name = split['name']
                start_date = split['start_date']
                end_date = split['end_date']
                teams = split['teams']
                
                # Get new player ID
                cursor.execute("SELECT id FROM players WHERE name = ?", (new_player_name,))
                result = cursor.fetchone()
                if not result:
                    print(f"   ❌ New player '{new_player_name}' not found")
                    continue
                
                new_player_id = result[0]
                
                # Update sub_match_participants for this time period and teams
                team_placeholders = ','.join(['?' for _ in teams])
                
                cursor.execute(f"""
                    UPDATE sub_match_participants 
                    SET player_id = ?
                    WHERE player_id = ?
                    AND sub_match_id IN (
                        SELECT sm.id 
                        FROM sub_matches sm
                        JOIN matches m ON sm.match_id = m.id
                        JOIN teams t ON t.id = CASE WHEN smp_inner.team_number = 1 THEN m.team1_id ELSE m.team2_id END
                        JOIN sub_match_participants smp_inner ON smp_inner.sub_match_id = sm.id
                        WHERE smp_inner.player_id = ?
                        AND m.match_date BETWEEN ? AND ?
                        AND t.name IN ({team_placeholders})
                    )
                """, [new_player_id, original_id, original_id, start_date, end_date] + teams)
                
                updated_count = cursor.rowcount
                total_updated += updated_count
                print(f"   ✅ Updated {updated_count} matches for {new_player_name}")
                print(f"      Period: {start_date[:10]} → {end_date[:10]}")
                print(f"      Teams: {', '.join(teams)}")
            
            # Check if original player has any remaining matches
            cursor.execute("SELECT COUNT(*) FROM sub_match_participants WHERE player_id = ?", (original_id,))
            remaining_matches = cursor.fetchone()[0]
            
            if remaining_matches > 0:
                print(f"   ⚠️  Original player '{original_name}' still has {remaining_matches} unassigned matches")
            else:
                print(f"   ✅ All matches successfully transferred from '{original_name}'")
            
            conn.commit()
            print(f"   📊 Total updated: {total_updated} sub_match_participants")
    
    def fix_player_temporal_overlaps(self, player_name, dry_run=True):
        """Fix a specific player's temporal overlaps"""
        print(f"🔧 {'Analyzing' if dry_run else 'Fixing'} temporal overlaps for '{player_name}'...")
        
        split_analysis = self.analyze_player_for_splitting(player_name)
        
        if not split_analysis:
            print(f"   ✅ No temporal overlaps found for '{player_name}'")
            return 0, []
        
        overlaps = split_analysis['overlaps']
        suggestions = split_analysis['split_suggestions']
        
        print(f"   ❌ Found {len(overlaps)} temporal overlaps")
        for overlap in overlaps:
            print(f"     - {overlap['club1']} vs {overlap['club2']}: {overlap['overlap_days']} days")
        
        print(f"   💡 Splitting into {len(suggestions)} players:")
        for suggestion in suggestions:
            print(f"     - '{suggestion['new_name']}': {suggestion['total_matches']} matches")
            print(f"       {suggestion['start'][:10]} → {suggestion['end'][:10]} ({suggestion['club']})")
        
        # Create split players
        created_players = self.create_split_players(split_analysis, dry_run)
        
        if not dry_run and created_players:
            # Update sub_match_participants
            self.update_sub_match_participants_temporal(player_name, created_players, dry_run)
        
        return len(created_players), created_players
    
    def fix_all_temporal_overlaps(self, dry_run=True, min_matches=50, min_teams=2):
        """Fix all players with temporal overlaps"""
        print(f"🚀 {'Analyzing' if dry_run else 'Fixing'} all temporal overlaps...")
        
        # Find problematic players
        problematic_players = self.detector.find_all_problematic_players(min_matches, min_teams)
        
        if not problematic_players:
            print("✅ No temporal overlaps found!")
            return 0, 0
        
        print(f"\n📋 Found {len(problematic_players)} players with temporal overlaps")
        
        total_players_fixed = 0
        total_new_players = 0
        
        for player_data in problematic_players:
            player_name = player_data['player']
            print(f"\n" + "="*60)
            
            created_count, created_players = self.fix_player_temporal_overlaps(player_name, dry_run)
            
            if created_count > 0:
                total_players_fixed += 1
                total_new_players += created_count
        
        print(f"\n📊 Summary:")
        print(f"   Players with overlaps: {len(problematic_players)}")
        print(f"   {'Would fix' if dry_run else 'Fixed'}: {total_players_fixed} players")
        print(f"   {'Would create' if dry_run else 'Created'}: {total_new_players} new split players")
        
        return total_players_fixed, total_new_players

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 temporal_overlap_fixer.py <command> [args...]")
        print("")
        print("Commands:")
        print("  analyze <player_name>              - Analyze how to split a player")
        print("  fix <player_name> [--force]        - Fix specific player's overlaps")
        print("  fix-all [min_matches] [--force]    - Fix all players with overlaps")
        print("")
        print("Examples:")
        print("  python3 temporal_overlap_fixer.py analyze 'Mikael Berg'")
        print("  python3 temporal_overlap_fixer.py fix 'Mikael Berg' --force")
        print("  python3 temporal_overlap_fixer.py fix-all 50 --force")
        return 1
    
    fixer = TemporalOverlapFixer()
    command = sys.argv[1]
    force = "--force" in sys.argv
    
    if command == "analyze":
        if len(sys.argv) < 3:
            print("Usage: analyze <player_name>")
            return 1
        
        player_name = sys.argv[2]
        split_analysis = fixer.analyze_player_for_splitting(player_name)
        
        if not split_analysis:
            print(f"✅ No temporal overlaps found for '{player_name}'")
            return 0
        
        overlaps = split_analysis['overlaps']
        suggestions = split_analysis['split_suggestions']
        
        print(f"🔍 Analysis for '{player_name}':")
        print(f"   Overlaps: {len(overlaps)}")
        for overlap in overlaps:
            print(f"     - {overlap['club1']} vs {overlap['club2']}: {overlap['overlap_days']} days")
        
        print(f"   Split suggestions: {len(suggestions)}")
        for suggestion in suggestions:
            print(f"     - '{suggestion['new_name']}'")
            print(f"       Period: {suggestion['start'][:10]} → {suggestion['end'][:10]}")
            print(f"       Club: {suggestion['club']}")
            print(f"       Teams: {', '.join(suggestion['teams'])}")
            print(f"       Matches: {suggestion['total_matches']}")
    
    elif command == "fix":
        if len(sys.argv) < 3:
            print("Usage: fix <player_name> [--force]")
            return 1
        
        player_name = sys.argv[2]
        created_count, created_players = fixer.fix_player_temporal_overlaps(player_name, dry_run=not force)
        
        if not force and created_count > 0:
            print(f"\n💡 Use --force to actually create {created_count} split players and fix overlaps")
    
    elif command == "fix-all":
        min_matches = 50
        for arg in sys.argv[2:]:
            if arg.isdigit():
                min_matches = int(arg)
        
        fixed_count, new_players = fixer.fix_all_temporal_overlaps(dry_run=not force, min_matches=min_matches)
        
        if not force and new_players > 0:
            print(f"\n💡 Use --force to actually fix {fixed_count} players and create {new_players} split players")
    
    else:
        print(f"Unknown command: {command}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())