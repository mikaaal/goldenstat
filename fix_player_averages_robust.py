#!/usr/bin/env python3
"""
Robust Player Average Fixer with better error handling and batch processing
"""
import requests
import json
import sqlite3
import sys
import time
from typing import Optional, Dict, List

class RobustPlayerAverageFixer:
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
            
            # Look for the specific sub-match
            for sub_match in data:
                # Match by the sub-match title/name
                if match_name in sub_match.get('title', ''):
                    stats_data = sub_match.get('statsData', [])
                    if not stats_data or not isinstance(stats_data, list):
                        continue
                        
                    for team_stats in stats_data:
                        order = team_stats.get('order', [])
                        for player_info in order:
                            if player_info.get('oname') == player_name:
                                # Calculate average from allScore and allDarts
                                all_score = team_stats.get('allScore', 0)
                                all_darts = team_stats.get('allDarts', 0)
                                # Only calculate if match is completed (has darts thrown)
                                if all_darts > 0 and all_score > 0:
                                    return (all_score / all_darts) * 3
            
            return None
            
        except Exception as e:
            print(f"❌ Error fetching player stats for {player_name}: {str(e)}")
            return None

    def fix_player_averages_batch(self, batch_size: int = 100, max_batches: Optional[int] = None):
        """Fix player averages in small batches to avoid I/O errors"""
        print("🚀 Starting robust player average fixing...")
        
        total_successful = 0
        total_failed = 0
        batch_num = 0
        
        while True:
            batch_num += 1
            
            if max_batches and batch_num > max_batches:
                print(f"🛑 Reached maximum batch limit: {max_batches}")
                break
            
            print(f"\n🔄 Processing batch {batch_num} (size: {batch_size})")
            
            # Get next batch
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT smp.id, smp.player_id, p.name, m.match_url, sm.match_name
                    FROM sub_match_participants smp
                    JOIN players p ON smp.player_id = p.id
                    JOIN sub_matches sm ON smp.sub_match_id = sm.id
                    JOIN matches m ON sm.match_id = m.id
                    WHERE smp.player_avg IS NULL 
                    AND m.match_url LIKE '%KQNP%'
                    AND sm.team1_legs + sm.team2_legs > 0
                    ORDER BY smp.id
                    LIMIT ?
                """, (batch_size,))
                
                participants = cursor.fetchall()
            
            if not participants:
                print("✅ No more participants to process!")
                break
            
            print(f"📊 Found {len(participants)} participants in this batch")
            
            # Process batch
            successful = 0
            failed = 0
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                for i, (participant_id, player_id, player_name, match_url, match_name) in enumerate(participants, 1):
                    print(f"[{i}/{len(participants)}] Fixing {player_name} in {match_name}...")
                    
                    player_avg = self.get_player_stats_from_api(match_url, player_name, match_name)
                    
                    if player_avg is not None:
                        try:
                            cursor.execute(
                                "UPDATE sub_match_participants SET player_avg = ? WHERE id = ?",
                                (player_avg, participant_id)
                            )
                            successful += 1
                            total_successful += 1
                            print(f"✅ Updated: {player_avg:.2f}")
                        except Exception as e:
                            failed += 1
                            total_failed += 1
                            print(f"❌ Database error: {e}")
                    else:
                        failed += 1
                        total_failed += 1
                        print(f"❌ Failed to get average")
                    
                    # Small delay to be nice to API
                    time.sleep(0.1)
                
                # Commit batch
                try:
                    conn.commit()
                    print(f"✅ Batch {batch_num} committed: {successful} successful, {failed} failed")
                except Exception as e:
                    print(f"❌ Batch commit error: {e}")
                    print(f"⚠️  Rolling back batch {batch_num}")
                    conn.rollback()
                    continue
            
            print(f"📊 Total progress: {total_successful} successful, {total_failed} failed")
            
            # Pause between batches
            time.sleep(1)
        
        print(f"\n🎉 Robust player average fixing completed!")
        print(f"📊 Final statistics: {total_successful} successful, {total_failed} failed")

def main():
    batch_size = 100
    max_batches = None
    
    if len(sys.argv) > 1:
        try:
            batch_size = int(sys.argv[1])
            print(f"🔧 Using batch size: {batch_size}")
        except ValueError:
            print("Usage: python fix_player_averages_robust.py [batch_size] [max_batches]")
            sys.exit(1)
    
    if len(sys.argv) > 2:
        try:
            max_batches = int(sys.argv[2])
            print(f"🔧 Maximum batches: {max_batches}")
        except ValueError:
            print("Usage: python fix_player_averages_robust.py [batch_size] [max_batches]")
            sys.exit(1)
    
    fixer = RobustPlayerAverageFixer()
    fixer.fix_player_averages_batch(batch_size, max_batches)

if __name__ == "__main__":
    main()