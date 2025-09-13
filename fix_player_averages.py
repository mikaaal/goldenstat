#!/usr/bin/env python3
"""
Fix player averages by recalculating from match data
"""
import requests
import json
import sqlite3
import sys
from typing import Optional, Dict, List

class PlayerAverageFixer:
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
            response = self.session.get(match_url, timeout=10)
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
                    if not isinstance(stats_data, list):
                        continue
                        
                    for team_stats in stats_data:
                        order = team_stats.get('order', [])
                        for player_info in order:
                            if player_info.get('oname') == player_name:
                                # Calculate average from allScore and allDarts
                                all_score = team_stats.get('allScore', 0)
                                all_darts = team_stats.get('allDarts', 0)
                                if all_darts > 0:
                                    return (all_score / all_darts) * 3
            
            return None
            
        except Exception as e:
            print(f"❌ Error fetching player stats for {player_name}: {str(e)}")
            return None

    def fix_all_player_averages(self, limit: Optional[int] = None):
        """Fix all player averages in database"""
        print("🚀 Starting player average fixing...")
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Get all sub_match_participants with NULL player_avg
            query = """
                SELECT smp.id, smp.player_id, p.name, m.match_url, sm.match_name
                FROM sub_match_participants smp
                JOIN players p ON smp.player_id = p.id
                JOIN sub_matches sm ON smp.sub_match_id = sm.id
                JOIN matches m ON sm.match_id = m.id
                WHERE smp.player_avg IS NULL
            """
            if limit:
                query += f" LIMIT {limit}"
                
            cursor.execute(query)
            participants = cursor.fetchall()
            
            print(f"📊 Found {len(participants)} participants needing average fixes")
            
            if not participants:
                print("✅ No participants need average fixing")
                return
            
            successful = 0
            failed = 0
            
            for i, (participant_id, player_id, player_name, match_url, match_name) in enumerate(participants, 1):
                print(f"\\n[{i}/{len(participants)}] Fixing {player_name} in {match_name}...")
                
                player_avg = self.get_player_stats_from_api(match_url, player_name, match_name)
                
                if player_avg is not None:
                    # Update player average
                    cursor.execute(
                        "UPDATE sub_match_participants SET player_avg = ? WHERE id = ?",
                        (player_avg, participant_id)
                    )
                    successful += 1
                    print(f"✅ Updated: {player_avg:.2f}")
                else:
                    failed += 1
                    print(f"❌ Failed to get average")
                
                # Progress update
                if i % 10 == 0:
                    print(f"\\n📊 Progress: {i}/{len(participants)}")
                    print(f"   ✅ Successful: {successful}")
                    print(f"   ❌ Failed: {failed}")
                    
                    # Commit progress
                    conn.commit()
            
            # Final commit
            conn.commit()
            
            print(f"\\n🎉 Player average fixing completed!")
            print(f"📊 Final statistics: {successful} successful, {failed} failed")

def main():
    limit = None
    if len(sys.argv) > 1:
        try:
            limit = int(sys.argv[1])
            print(f"🔧 Processing first {limit} participants only")
        except ValueError:
            print("Usage: python fix_player_averages.py [limit]")
            sys.exit(1)
    
    fixer = PlayerAverageFixer()
    fixer.fix_all_player_averages(limit)

if __name__ == "__main__":
    main()