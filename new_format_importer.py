#!/usr/bin/env python3
"""
New Format Importer for N01 Darts API Data
Handles the parsing of match data from the new API format
"""
import requests
import json
import sqlite3
from datetime import datetime
from typing import Dict, List, Optional, Any
from database import DartDatabase

class NewFormatImporter:
    def __init__(self, db_path: str = "goldenstat.db"):
        self.db = DartDatabase(db_path)
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Accept-Language': 'en-US,en;q=0.9,sv;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'X-Requested-With': 'XMLHttpRequest'
        })

    def fetch_match_data(self, url: str) -> Optional[List[Dict]]:
        """Fetch match data from URL and return parsed JSON"""
        try:
            response = self.session.get(url, timeout=10)
            if response.status_code != 200:
                print(f"❌ HTTP {response.status_code} for {url}")
                return None
            
            data = response.json()
            if not data:
                print(f"❌ Empty response for {url}")
                return None
                
            return data
        except Exception as e:
            print(f"❌ Error fetching {url}: {e}")
            return None

    def process_match_from_url(self, url: str) -> bool:
        """Process a match from URL and import into database"""
        print(f"🎯 Processing match from {url}")
        
        match_data = self.fetch_match_data(url)
        if not match_data:
            return False
        
        # Extract match information
        match_info = self.extract_match_from_new_format(match_data)
        if not match_info:
            return False
        
        # Get match date from API
        match_date = self.extract_match_date_from_api(match_data)
        if match_date:
            match_info['match_date'] = match_date
        
        try:
            # Import into database
            match_id, is_new = self.db.insert_match({
                'team1_name': match_info['team1']['name'],
                'team2_name': match_info['team2']['name'],
                'team1_legs': match_info['team1_legs'],
                'team2_legs': match_info['team2_legs'],
                'team1_avg': match_info.get('team1_avg'),
                'team2_avg': match_info.get('team2_avg'),
                'match_date': match_info.get('match_date'),
                'match_url': url
            })
            
            # Process sub-matches
            for sub_match_info in match_info['sub_matches']:
                self.import_sub_match(match_id, sub_match_info, url)
            
            print(f"✅ Successfully imported match {match_id}")
            return True
            
        except Exception as e:
            print(f"❌ Error importing match: {e}")
            return False

    def extract_match_date_from_api(self, match_data: List[Dict]) -> Optional[datetime]:
        """Extract match date from API startTime"""
        try:
            if match_data and len(match_data) > 0:
                start_time = match_data[0].get('startTime', 0)
                if start_time > 0:
                    return datetime.fromtimestamp(start_time)
        except Exception as e:
            print(f"❌ Error extracting match date: {e}")
        return None

    def extract_match_from_new_format(self, match_data: List[Dict]) -> Optional[Dict]:
        """Extract standardized match data from new API format"""
        if not match_data:
            return None
        
        try:
            # Initialize counters
            team1_total_legs = 0
            team2_total_legs = 0
            team1_total_score = 0
            team1_total_darts = 0
            team2_total_score = 0
            team2_total_darts = 0
            
            # Extract team names from first sub-match
            first_match = match_data[0]
            team1_name = first_match.get('team1', {}).get('name', 'Team 1')
            team2_name = first_match.get('team2', {}).get('name', 'Team 2')
            match_date = datetime.now()  # Default, will be overridden by API data
            
            sub_matches = []
            
            # Process each sub-match
            for sub_match_data in match_data:
                title = sub_match_data.get('title', '')
                team1_legs = sub_match_data.get('team1', {}).get('legCount', 0)
                team2_legs = sub_match_data.get('team2', {}).get('legCount', 0)
                
                # Update total legs
                team1_total_legs += team1_legs
                team2_total_legs += team2_legs
                
                # Calculate averages from statsData if available
                stats_data = sub_match_data.get('statsData', [])
                if len(stats_data) >= 2:
                    team1_total_score += stats_data[0].get('allScore', 0)
                    team1_total_darts += stats_data[0].get('allDarts', 0)
                    team2_total_score += stats_data[1].get('allScore', 0)
                    team2_total_darts += stats_data[1].get('allDarts', 0)
                
                # Create sub-match entry
                sub_match = {
                    'match_name': title,
                    'match_type': self.determine_match_type(title),
                    'team1_legs': team1_legs,
                    'team2_legs': team2_legs,
                    'team1_players': self.extract_players_from_new_format(sub_match_data.get('statsData', [{}])[0]),
                    'team2_players': self.extract_players_from_new_format(sub_match_data.get('statsData', [{}])[1] if len(sub_match_data.get('statsData', [])) > 1 else {}),
                    'legs': self.extract_legs_from_new_format(sub_match_data)
                }
                sub_matches.append(sub_match)
            
            # Calculate overall team averages
            team1_avg = (team1_total_score / team1_total_darts * 3) if team1_total_darts > 0 else None
            team2_avg = (team2_total_score / team2_total_darts * 3) if team2_total_darts > 0 else None
            
            # Return standardized match format
            return {
                'team1': {'name': team1_name},
                'team2': {'name': team2_name},
                'team1_legs': team1_total_legs,
                'team2_legs': team2_total_legs,
                'team1_avg': team1_avg,
                'team2_avg': team2_avg,
                'match_date': match_date,
                'sub_matches': sub_matches
            }
            
        except Exception as e:
            print(f"❌ Error extracting match data: {e}")
            return None

    def extract_players_from_new_format(self, stats_data: Dict) -> List[Dict]:
        """Extract player information from new format statsData"""
        players = []
        order = stats_data.get('order', [])
        
        # Calculate average from allScore and allDarts if available
        all_score = stats_data.get('allScore', 0)
        all_darts = stats_data.get('allDarts', 0)
        player_avg = None
        if all_darts > 0:
            # Calculate per-dart average, then multiply by 3 for dart standard
            player_avg = (all_score / all_darts) * 3
        
        if order:
            for player_info in order:
                players.append({
                    'name': player_info.get('oname', 'Unknown'),
                    'avg': player_avg
                })
        
        return players

    def extract_legs_from_new_format(self, sub_match_data: Dict) -> List[Dict]:
        """Extract leg data from new format"""
        legs = []
        leg_data_list = sub_match_data.get('legData', [])
        
        for leg_num, leg_data in enumerate(leg_data_list, 1):
            if leg_data.get('endFlag') != 1:  # Skip incomplete legs
                continue
                
            # Determine winner based on who finished (remaining score = 0)
            winner_team = self.determine_leg_winner(leg_data)
            
            # Extract throws using corrected logic
            throws = self.extract_corrected_throws_from_leg(leg_data)
            
            legs.append({
                'leg_number': leg_num,
                'winner_team': winner_team,
                'throws': throws
            })
        
        return legs

    def determine_leg_winner(self, leg_data: Dict) -> int:
        """Determine which team won the leg"""
        winner = leg_data.get('winner', 0)
        return winner + 1  # Convert 0-based to 1-based

    def extract_corrected_throws_from_leg(self, leg_data: Dict) -> List[Dict]:
        """Extract throws with corrected finish scores"""
        throws = []
        player_data = leg_data.get('playerData', [[], []])
        
        if len(player_data) < 2:
            return throws
        
        # Get who starts first (0 = team 1 starts, 1 = team 2 starts)
        first_player = leg_data.get('first', 0)
        
        # Get max throws from both players
        max_throws_team1 = len(player_data[0])
        max_throws_team2 = len(player_data[1])
        total_throws = max_throws_team1 + max_throws_team2
        
        # Create alternating sequence
        team1_index = 0
        team2_index = 0
        previous_remaining = [501, 501]  # Track remaining score for each team
        
        for throw_sequence in range(total_throws):
            # Determine which team throws based on starting player and sequence
            if (first_player == 0 and throw_sequence % 2 == 0) or (first_player == 1 and throw_sequence % 2 == 1):
                # Team 1's turn
                if team1_index < max_throws_team1:
                    throw_data = player_data[0][team1_index]
                    if throw_data.get('score', -1) >= -3:  # Valid throw (including finishes with negative scores)
                        remaining_score = throw_data.get('left', 501)
                        api_score = throw_data.get('score', 0)
                        
                        # Calculate actual score for finishes
                        if remaining_score == 0 and api_score < 0:
                            # This is a finish - calculate the actual checkout score
                            actual_score = previous_remaining[0]  # The checkout value is what they had remaining
                            darts_used = -api_score  # Negative score indicates darts used
                        else:
                            # Regular throw
                            actual_score = api_score
                            darts_used = 3
                        
                        throws.append({
                            'team_number': 1,
                            'round_number': (throw_sequence // 2) + 1,
                            'score': actual_score,
                            'remaining_score': remaining_score,
                            'darts_used': darts_used
                        })
                        
                        # Update previous remaining score
                        previous_remaining[0] = remaining_score
                        
                    team1_index += 1
                else:
                    break
            else:
                # Team 2's turn
                if team2_index < max_throws_team2:
                    throw_data = player_data[1][team2_index]
                    if throw_data.get('score', -1) >= -3:  # Valid throw (including finishes with negative scores)
                        remaining_score = throw_data.get('left', 501)
                        api_score = throw_data.get('score', 0)
                        
                        # Calculate actual score for finishes
                        if remaining_score == 0 and api_score < 0:
                            # This is a finish - calculate the actual checkout score
                            actual_score = previous_remaining[1]  # The checkout value is what they had remaining
                            darts_used = -api_score  # Negative score indicates darts used
                        else:
                            # Regular throw
                            actual_score = api_score
                            darts_used = 3
                        
                        throws.append({
                            'team_number': 2,
                            'round_number': (throw_sequence // 2) + 1,
                            'score': actual_score,
                            'remaining_score': remaining_score,
                            'darts_used': darts_used
                        })
                        
                        # Update previous remaining score
                        previous_remaining[1] = remaining_score
                        
                    team2_index += 1
                else:
                    break
        
        return throws

    def determine_match_type(self, title: str) -> str:
        """Determine match type from title"""
        if 'Singles' in title:
            return 'Singles'
        elif 'Doubles' in title:
            return 'Doubles'
        else:
            return 'Unknown'

    def import_sub_match(self, match_id: int, sub_match_info: Dict, match_url: str):
        """Import a sub-match into the database"""
        try:
            # Insert sub-match
            sub_match_id = self.db.insert_sub_match({
                'match_id': match_id,
                'match_name': sub_match_info['match_name'],
                'match_type': sub_match_info['match_type'],
                'team1_legs': sub_match_info['team1_legs'],
                'team2_legs': sub_match_info['team2_legs']
            })
            
            # Insert players and participants
            team1_players = sub_match_info.get('team1_players', [])
            team2_players = sub_match_info.get('team2_players', [])
            
            for player_info in team1_players:
                player_id = self.db.insert_player({'name': player_info['name']})
                self.db.insert_participant({
                    'sub_match_id': sub_match_id,
                    'player_id': player_id,
                    'team_number': 1,
                    'player_avg': player_info.get('avg')
                })
            
            for player_info in team2_players:
                player_id = self.db.insert_player({'name': player_info['name']})
                self.db.insert_participant({
                    'sub_match_id': sub_match_id,
                    'player_id': player_id,
                    'team_number': 2,
                    'player_avg': player_info.get('avg')
                })
            
            # Insert legs and throws
            for leg_info in sub_match_info.get('legs', []):
                leg_id = self.db.insert_leg({
                    'sub_match_id': sub_match_id,
                    'leg_number': leg_info['leg_number'],
                    'winner_team': leg_info['winner_team']
                })
                
                for throw_info in leg_info.get('throws', []):
                    self.db.insert_throw({
                        'leg_id': leg_id,
                        'team_number': throw_info['team_number'],
                        'round_number': throw_info['round_number'],
                        'score': throw_info['score'],
                        'remaining_score': throw_info['remaining_score'],
                        'darts_used': throw_info['darts_used']
                    })
            
        except Exception as e:
            print(f"❌ Error importing sub-match: {e}")
            raise