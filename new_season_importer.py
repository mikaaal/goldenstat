#!/usr/bin/env python3
"""
New Season Importer for 2025/2026 season
Uses the new API endpoints for importing match data
"""
import requests
import json
import time
from itertools import combinations
from typing import List, Dict, Optional, Any
from datetime import datetime
from database import DartDatabase

class NewSeasonImporter:
    def __init__(self, db_path: str = "goldenstat.db"):
        self.db = DartDatabase(db_path)
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin'
        })
    
    def get_team_ids(self, tdid: str) -> List[str]:
        """Get all team IDs from division"""
        stats_url = f'https://tk2-228-23746.vs.sakura.ne.jp/n01/tournament/n01_tournament.php?cmd=get_lg_stats_list&tdid={tdid}'
        
        try:
            print(f"🔍 Fetching team IDs for division {tdid}...")
            response = self.session.get(stats_url, timeout=15)
            
            if response.status_code == 200:
                data = response.json()[0]  # First element contains the team data
                team_ids = list(data.keys())
                print(f"✅ Found {len(team_ids)} teams: {team_ids}")
                return team_ids
            else:
                print(f"❌ Failed to fetch team IDs: {response.status_code}")
                return []
                
        except Exception as e:
            print(f"❌ Error fetching team IDs: {e}")
            return []
    
    def get_round_codes(self, tdid: str) -> List[str]:
        """Get all round codes from the schedule API"""
        try:
            print(f"🔍 Fetching round codes for division {tdid}...")
            
            schedule_url = 'https://tk2-228-23746.vs.sakura.ne.jp/n01/tournament/n01_tournament.php?cmd=get_lg_schedule'
            payload = {'tdid': tdid, 'div': 0}
            
            response = self.session.post(schedule_url, json=payload, timeout=15)
            
            if response.status_code == 200:
                schedule_data = response.json()
                
                # Extract unique round codes
                round_codes = set()
                for match in schedule_data:
                    if 'lsid' in match:
                        round_codes.add(match['lsid'])
                
                round_codes = sorted(list(round_codes))
                print(f"✅ Found {len(round_codes)} unique round codes")
                return round_codes
            else:
                print(f"❌ Failed to fetch round codes: {response.status_code}")
                return ['i0ts', 'mljp', 's3n5']  # Fallback to known codes
                
        except Exception as e:
            print(f"❌ Error fetching round codes: {e}")
            return ['i0ts', 'mljp', 's3n5']  # Fallback to known codes

    def get_scheduled_matches(self, tdid: str) -> List[Dict[str, str]]:
        """Get all scheduled matches with exact team pairings from schedule API"""
        try:
            print(f"🔍 Fetching scheduled matches for division {tdid}...")
            
            schedule_url = 'https://tk2-228-23746.vs.sakura.ne.jp/n01/tournament/n01_tournament.php?cmd=get_lg_schedule'
            payload = {'tdid': tdid, 'div': 0}
            
            response = self.session.post(schedule_url, json=payload, timeout=15)
            
            if response.status_code == 200:
                schedule_data = response.json()
                
                # Extract match pairings with round codes
                matches = []
                for match in schedule_data:
                    if 'p' in match and 'lsid' in match and len(match['p']) == 2:
                        matches.append({
                            'team1': match['p'][0],
                            'team2': match['p'][1],
                            'round_code': match['lsid'],
                            'round_title': match.get('t', '')
                        })
                
                print(f"✅ Found {len(matches)} scheduled matches")
                return matches
            else:
                print(f"❌ Failed to fetch schedule: {response.status_code}")
                return []
                
        except Exception as e:
            print(f"❌ Error fetching schedule: {e}")
            return []

    def generate_match_urls(self, tdid: str) -> List[str]:
        """Generate match URLs based on actual scheduled matches"""
        base_url = 'https://tk2-228-23746.vs.sakura.ne.jp/n01/tournament/n01_online_t.php?cmd=get_setdata&tmid='
        match_urls = []
        
        # Get actual scheduled matches
        scheduled_matches = self.get_scheduled_matches(tdid)
        
        for match in scheduled_matches:
            # Generate both possible team orderings since we don't know which is home/away
            url1 = f'{base_url}{tdid}_lg_0_{match["round_code"]}_{match["team1"]}_{match["team2"]}'
            url2 = f'{base_url}{tdid}_lg_0_{match["round_code"]}_{match["team2"]}_{match["team1"]}'
            match_urls.extend([url1, url2])
        
        print(f"📋 Generated {len(match_urls)} match URLs from {len(scheduled_matches)} scheduled matches")
        return match_urls
    
    def fetch_match_data(self, match_url: str) -> Optional[Dict[str, Any]]:
        """Fetch match data from URL"""
        try:
            response = self.session.get(match_url, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                if data and len(data) > 0:  # Check if match exists and has data
                    return data
                else:
                    return None  # Empty response means no match
            else:
                return None
                
        except Exception as e:
            print(f"❌ Error fetching {match_url}: {e}")
            return None
    
    def extract_match_info(self, match_data: List[Dict], season: str = "2025/2026") -> Dict[str, Any]:
        """Extract match information from API response"""
        if not match_data:
            return {}
        
        # Get basic info from first sub-match
        first_submatch = match_data[0]
        
        # Extract teams from statsData
        stats_data = first_submatch.get('statsData', [])
        if len(stats_data) < 2:
            return {}
        
        team1_name = stats_data[0]['name']
        team2_name = stats_data[1]['name']
        
        # Calculate match date from timestamp
        start_time = first_submatch.get('startTime', 0)
        if start_time > 1000000000000:  # Milliseconds
            start_time = start_time / 1000
        match_date = datetime.fromtimestamp(start_time)
        
        # Extract season and division from title
        title = first_submatch.get('title', '')
        # Season is passed as parameter
        division = "Unknown"
        
        if 'Division' in title:
            parts = title.split('Division')
            if len(parts) > 1:
                division = parts[1].strip().split()[0]
        
        # Calculate team scores (wins per team across all sub-matches)
        team1_wins = 0
        team2_wins = 0
        
        for submatch in match_data:
            stats = submatch.get('statsData', [])
            if len(stats) >= 2:
                team1_wins += stats[0].get('winSets', 0)
                team2_wins += stats[1].get('winSets', 0)
        
        # Calculate team averages
        team1_total_score = 0
        team1_total_darts = 0
        team2_total_score = 0
        team2_total_darts = 0
        
        for submatch in match_data:
            stats = submatch.get('statsData', [])
            if len(stats) >= 2:
                team1_total_score += stats[0].get('allScore', 0)
                team1_total_darts += stats[0].get('allDarts', 0)
                team2_total_score += stats[1].get('allScore', 0)
                team2_total_darts += stats[1].get('allDarts', 0)
        
        team1_avg = round((team1_total_score / max(1, team1_total_darts)) * 3, 2) if team1_total_darts > 0 else 0
        team2_avg = round((team2_total_score / max(1, team2_total_darts)) * 3, 2) if team2_total_darts > 0 else 0
        
        return {
            'team1_name': team1_name,
            'team2_name': team2_name,
            'team1_score': team1_wins,
            'team2_score': team2_wins,
            'team1_avg': team1_avg,
            'team2_avg': team2_avg,
            'match_date': match_date,
            'season': season,
            'division': division,
            'match_url': first_submatch.get('tmid', ''),
            'sub_matches': match_data
        }
    
    def import_match(self, match_info: Dict[str, Any]) -> bool:
        """Import a single match into database"""
        try:
            # Get or create teams
            team1_id = self.db.get_or_create_team(match_info['team1_name'], match_info['division'])
            team2_id = self.db.get_or_create_team(match_info['team2_name'], match_info['division'])
            
            # Insert main match
            match_data = {
                'match_url': match_info['match_url'],
                'team1_id': team1_id,
                'team2_id': team2_id,
                'team1_score': match_info['team1_score'],
                'team2_score': match_info['team2_score'],
                'team1_avg': match_info['team1_avg'],
                'team2_avg': match_info['team2_avg'],
                'division': match_info['division'],
                'season': match_info['season'],
                'match_date': match_info['match_date']
            }
            
            match_id, is_new = self.db.insert_match(match_data)
            
            # Process each sub-match
            for submatch in match_info['sub_matches']:
                self.import_submatch(match_id, submatch, team1_id, team2_id)
            
            return True
            
        except Exception as e:
            print(f"❌ Error importing match: {e}")
            return False
    
    def import_submatch(self, match_id: int, submatch_data: Dict, team1_id: int, team2_id: int):
        """Import a sub-match with its legs and throws"""
        try:
            # Extract sub-match info
            title = submatch_data.get('title', '')
            # AD (Avgörande Dubbel) is always Doubles
            if 'Doubles' in title or ' AD' in title or title.endswith('AD'):
                match_type = 'Doubles'
            else:
                match_type = 'Singles'
            
            # Get match name from title
            match_name = title
            
            # Get leg wins for each team
            stats = submatch_data.get('statsData', [])
            team1_legs = stats[0].get('winLegs', 0) if len(stats) > 0 else 0
            team2_legs = stats[1].get('winLegs', 0) if len(stats) > 1 else 0
            
            # Calculate averages for this sub-match
            team1_avg = 0
            team2_avg = 0
            if len(stats) >= 2:
                team1_score = stats[0].get('allScore', 0)
                team1_darts = stats[0].get('allDarts', 0)
                team2_score = stats[1].get('allScore', 0)
                team2_darts = stats[1].get('allDarts', 0)
                
                team1_avg = round((team1_score / max(1, team1_darts)) * 3, 2) if team1_darts > 0 else 0
                team2_avg = round((team2_score / max(1, team2_darts)) * 3, 2) if team2_darts > 0 else 0
            
            # Insert sub-match
            sub_match_data = {
                'match_id': match_id,
                'match_number': 1,
                'match_type': match_type,
                'match_name': match_name,
                'team1_legs': team1_legs,
                'team2_legs': team2_legs,
                'team1_avg': team1_avg,
                'team2_avg': team2_avg,
                'mid': submatch_data.get('mid', '')
            }
            
            sub_match_id = self.db.insert_sub_match(sub_match_data)
            
            # Import players
            self.import_players(sub_match_id, stats, team1_id, team2_id)
            
            # Import legs and throws
            leg_data_list = submatch_data.get('legData', [])
            for leg_index, leg_data in enumerate(leg_data_list, 1):
                self.import_leg(sub_match_id, leg_index, leg_data)
            
        except Exception as e:
            print(f"❌ Error importing sub-match: {e}")
    
    def import_players(self, sub_match_id: int, stats_data: List[Dict], team1_id: int, team2_id: int):
        """Import players for this sub-match"""
        try:
            for team_index, team_stats in enumerate(stats_data):
                team_number = team_index + 1
                player_avg = 0
                
                # Calculate player average
                all_score = team_stats.get('allScore', 0)
                all_darts = team_stats.get('allDarts', 0)
                if all_darts > 0:
                    player_avg = round((all_score / all_darts) * 3, 2)
                
                # Get player names from order
                order = team_stats.get('order', [])
                for player_info in order:
                    player_name = player_info.get('oname', 'Unknown')
                    player_id = self.db.get_or_create_player(player_name)
                    
                    # Insert participant
                    participant_data = {
                        'sub_match_id': sub_match_id,
                        'player_id': player_id,
                        'team_number': team_number,
                        'player_avg': player_avg
                    }
                    
                    self.db.insert_sub_match_participant(participant_data)
                    
        except Exception as e:
            print(f"❌ Error importing players: {e}")
    
    def import_leg(self, sub_match_id: int, leg_number: int, leg_data: Dict):
        """Import a single leg with its throws"""
        try:
            # Determine winner
            winner_team = leg_data.get('winner', 0) + 1  # Convert 0/1 to 1/2
            first_player_team = leg_data.get('first', 0) + 1
            
            # Insert leg
            leg_info = {
                'sub_match_id': sub_match_id,
                'leg_number': leg_number,
                'winner_team': winner_team,
                'first_player_team': first_player_team,
                'total_rounds': leg_data.get('currentRound', 0)
            }
            
            leg_id = self.db.insert_leg(leg_info)
            
            # Import throws
            player_data = leg_data.get('playerData', [])
            for team_index, team_throws in enumerate(player_data):
                team_number = team_index + 1
                
                for round_index, throw_data in enumerate(team_throws, 1):
                    score = throw_data.get('score', 0)
                    remaining = throw_data.get('left', 501)
                    
                    # Determine darts used
                    darts_used = 3  # Default
                    if score < 0:
                        darts_used = abs(score)  # Negative score indicates darts used to finish
                        score = remaining + abs(score)  # Calculate actual score
                    
                    throw_info = {
                        'leg_id': leg_id,
                        'team_number': team_number,
                        'round_number': round_index,
                        'score': score,
                        'remaining_score': remaining,
                        'darts_used': darts_used
                    }
                    
                    self.db.insert_throw(throw_info)
                    
        except Exception as e:
            print(f"❌ Error importing leg: {e}")
    
    def load_urls_from_file(self, file_path: str) -> List[str]:
        """Load match URLs from a file"""
        try:
            print(f"📂 Loading URLs from {file_path}")
            with open(file_path, 'r', encoding='utf-8') as f:
                urls = []
                for line in f:
                    line = line.strip()
                    # Skip comments and empty lines
                    if line and not line.startswith('#'):
                        urls.append(line)
                
                print(f"✅ Loaded {len(urls)} URLs from file")
                return urls
                
        except FileNotFoundError:
            print(f"❌ File not found: {file_path}")
            return []
        except Exception as e:
            print(f"❌ Error loading URLs from file: {e}")
            return []

    def import_division(self, tdid: str, url_file: str = None, season: str = "2025/2026") -> Dict[str, int]:
        """Import all matches from a division"""
        print(f"\n🎯 Starting import for division {tdid}")
        
        if url_file:
            # Load URLs from file
            match_urls = self.load_urls_from_file(url_file)
        else:
            # Generate match URLs from scheduled matches (fallback)
            print("📋 No URL file specified, generating URLs from API...")
            match_urls = self.generate_match_urls(tdid)
        
        success_count = 0
        failed_count = 0
        
        for i, match_url in enumerate(match_urls, 1):
            print(f"\n📊 Processing match {i}/{len(match_urls)}")
            print(f"🔗 URL: {match_url}")
            
            try:
                # Fetch match data
                match_data = self.fetch_match_data(match_url)
                
                if match_data:
                    # Extract match info
                    match_info = self.extract_match_info(match_data, season)
                    
                    if match_info:
                        # Import to database
                        success = self.import_match(match_info)
                        
                        if success:
                            success_count += 1
                            print(f"✅ Match imported: {match_info['team1_name']} vs {match_info['team2_name']}")
                        else:
                            failed_count += 1
                            print(f"❌ Failed to import match")
                    else:
                        # No match data, skip silently (probably non-existent match combo)
                        continue
                else:
                    # No match data, skip silently
                    continue
                    
            except Exception as e:
                failed_count += 1
                print(f"❌ Error processing match {i}: {e}")
            
            # Add small delay to be respectful
            time.sleep(1)
        
        print(f"\n✅ Division {tdid} import completed:")
        print(f"   Success: {success_count}")
        print(f"   Failed: {failed_count}")
        
        return {"success": success_count, "failed": failed_count, "total": success_count + failed_count}

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 new_season_importer.py <division_id> [url_file] [season]")
        print("Example: python3 new_season_importer.py t_jM8s_0341")
        print("Example: python3 new_season_importer.py t_jM8s_0341 t_jM8s_0341_match_urls.txt")
        print("Example: python3 new_season_importer.py t_jM8s_0341 t_jM8s_0341_match_urls.txt 2023/2024")
        return 1
    
    division_id = sys.argv[1]
    url_file = sys.argv[2] if len(sys.argv) > 2 else None
    season = sys.argv[3] if len(sys.argv) > 3 else "2025/2026"
    
    importer = NewSeasonImporter()
    result = importer.import_division(division_id, url_file, season)
    
    print(f"\n🎯 Final Result:")
    print(f"   ✅ Successful imports: {result['success']}")
    print(f"   ❌ Failed imports: {result['failed']}")
    print(f"   📊 Total processed: {result['total']}")
    
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())