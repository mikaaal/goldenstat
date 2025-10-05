#!/usr/bin/env python3
"""
Comprehensive Player Average Fixer for ALL tournaments
Fixes the previous script's limitation of only processing KQNP matches
"""
import requests
import json
import sqlite3
import sys
import time
from typing import Optional, Dict, List

class ComprehensivePlayerAverageFixer:
    def __init__(self, db_path: str = "goldenstat.db"):
        self.db_path = db_path
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Accept-Language': 'en-US,en;q=0.9,sv;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'X-Requested-With': 'XMLHttpRequest'
        })

    def get_player_stats_from_api(self, match_url: str, player_name: str, match_name: str) -> Optional[float]:
        """Get player average from API statsData for specific sub-match"""
        try:
            response = self.session.get(match_url, timeout=20)
            if response.status_code != 200:
                return None
                
            data = response.json()
            if not data:
                return None
            
            # Handle the new array format from Ey7h tournament
            if isinstance(data, list):
                for match in data:
                    if isinstance(match, dict) and 'statsData' in match:
                        stats_data_list = match['statsData']
                        if isinstance(stats_data_list, list):
                            for stats_data in stats_data_list:
                                if isinstance(stats_data, dict):
                                    # Check if this is the team/player we're looking for
                                    team_name = stats_data.get('name', '')
                                    # Look for individual players in the 'order' array
                                    if 'order' in stats_data and isinstance(stats_data['order'], list):
                                        for player in stats_data['order']:
                                            if isinstance(player, dict) and player.get('oname') == player_name:
                                                all_score = stats_data.get('allScore', 0)
                                                all_darts = stats_data.get('allDarts', 0)
                                                if all_darts > 0:
                                                    return (all_score / all_darts) * 3
                return None
            
            # Handle the old format with playersData
            if 'playersData' in data:
                players_data = data['playersData']
                
                # Handle both array and object formats
                if isinstance(players_data, list):
                    players_dict = {}
                    for player_data in players_data:
                        if isinstance(player_data, dict) and 'name' in player_data:
                            players_dict[player_data['name']] = player_data
                    players_data = players_dict
                elif isinstance(players_data, dict):
                    # Check if it's in numbered format like {"0": {...}, "1": {...}}
                    if all(k.isdigit() for k in players_data.keys()):
                        new_dict = {}
                        for player_data in players_data.values():
                            if isinstance(player_data, dict) and 'name' in player_data:
                                new_dict[player_data['name']] = player_data
                        players_data = new_dict
                
                if player_name not in players_data:
                    return None
                    
                player_data = players_data[player_name]
                stats_data = player_data.get('statsData', {})
                
                if not stats_data:
                    return None
                    
                all_score = stats_data.get('allScore', 0)
                all_darts = stats_data.get('allDarts', 0)
                
                if all_darts > 0:
                    # Calculate average per 3 darts (dart standard)
                    return (all_score / all_darts) * 3
            
            return None
            
        except Exception as e:
            print(f"❌ Error fetching player stats for {player_name}: {e}")
            return None

    def fix_batch(self, batch_size: int = 50) -> tuple:
        """Fix a batch of participants and return (successful, failed) counts"""
        successful = 0
        failed = 0
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Get next batch of participants with missing averages
            # Remove the KQNP filter to process ALL tournaments
            cursor.execute("""
                SELECT 
                    smp.id,
                    p.name,
                    m.match_url,
                    sm.match_name
                FROM sub_match_participants smp
                JOIN players p ON smp.player_id = p.id
                JOIN sub_matches sm ON smp.sub_match_id = sm.id
                JOIN matches m ON sm.match_id = m.id
                WHERE smp.player_avg IS NULL 
                AND sm.team1_legs + sm.team2_legs > 0
                ORDER BY smp.id
                LIMIT ?
            """, (batch_size,))
            
            participants = cursor.fetchall()
            
            if not participants:
                return (0, 0)
            
            print(f"📊 Found {len(participants)} participants in this batch")
            
            # Process each participant
            for participant_id, player_name, match_url, match_name in participants:
                print(f"[{successful + failed + 1}/{len(participants)}] Fixing {player_name} in {match_name}...")
                
                try:
                    # Get player average from API
                    player_avg = self.get_player_stats_from_api(match_url, player_name, match_name)
                    
                    if player_avg is not None:
                        # Update database
                        cursor.execute("""
                            UPDATE sub_match_participants 
                            SET player_avg = ? 
                            WHERE id = ?
                        """, (player_avg, participant_id))
                        
                        print(f"✅ Updated {player_name}: {player_avg:.2f}")
                        successful += 1
                    else:
                        print(f"❌ Failed to get average")
                        failed += 1
                        
                except Exception as e:
                    print(f"❌ Error processing {player_name}: {e}")
                    failed += 1
                
                # Small delay to be respectful to the API
                time.sleep(0.1)
            
            # Commit the batch
            conn.commit()
            print(f"✅ Batch committed: {successful} successful, {failed} failed")
            
        return (successful, failed)

    def run(self, batch_size: int = 50, max_batches: int = None):
        """Run the comprehensive fixing process"""
        print("🚀 Starting Comprehensive Player Average Fixer...")
        print("📋 Processing ALL tournaments (not just KQNP)")
        
        total_successful = 0
        total_failed = 0
        batch_count = 0
        
        while True:
            batch_count += 1
            print(f"\n🔄 Processing batch {batch_count} (size: {batch_size})")
            
            successful, failed = self.fix_batch(batch_size)
            total_successful += successful
            total_failed += failed
            
            print(f"📊 Total progress: {total_successful} successful, {total_failed} failed")
            
            # Stop if no more participants to process
            if successful == 0 and failed == 0:
                print("✅ No more participants to process!")
                break
                
            # Stop if max batches reached
            if max_batches and batch_count >= max_batches:
                print(f"⏹️ Reached maximum batch limit ({max_batches})")
                break
        
        print(f"\n🎉 Final results: {total_successful} successful, {total_failed} failed")

if __name__ == "__main__":
    fixer = ComprehensivePlayerAverageFixer()
    
    # Get batch size from command line argument
    batch_size = int(sys.argv[1]) if len(sys.argv) > 1 else 50
    max_batches = int(sys.argv[2]) if len(sys.argv) > 2 else None
    
    fixer.run(batch_size, max_batches)