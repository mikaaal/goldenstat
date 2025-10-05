#!/usr/bin/env python3
"""
Fix finish scores in database by recalculating from match API data
"""
import requests
import json
import sqlite3
import sys
from typing import Optional, Dict, List

class FinishScoreFixer:
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

    def get_corrected_finishes_from_api(self, match_url: str, sub_match_name: str) -> List[Dict]:
        """Get corrected finish data from API"""
        try:
            response = self.session.get(match_url, timeout=10)
            if response.status_code != 200:
                return []
            
            data = response.json()
            if not data:
                return []
            
            # Find the specific sub-match
            for sub_match in data:
                if sub_match_name in sub_match.get('title', ''):
                    leg_data_list = sub_match.get('legData', [])
                    corrected_finishes = []
                    
                    for leg_num, leg_data in enumerate(leg_data_list, 1):
                        if leg_data.get('endFlag') == 1:  # Only completed legs
                            throws = self.extract_corrected_throws_from_leg(leg_data)
                            
                            # Find finishes in this leg
                            for throw in throws:
                                if throw['remaining_score'] == 0:
                                    corrected_finishes.append({
                                        'leg_number': leg_num,
                                        'team_number': throw['team_number'],
                                        'round_number': throw['round_number'],
                                        'score': throw['score'],
                                        'darts_used': throw['darts_used']
                                    })
                    
                    return corrected_finishes
            
            return []
            
        except Exception as e:
            print(f"❌ Error fetching corrected finishes: {str(e)}")
            return []

    def fix_all_finish_scores(self, limit: Optional[int] = None):
        """Fix all finish scores in database"""
        print("🚀 Starting finish score fixing...")
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Get all throws that are finishes (remaining_score = 0) with negative scores
            query = """
                SELECT DISTINCT 
                    t.id, t.score, t.darts_used, t.team_number, t.round_number,
                    l.leg_number, l.id as leg_id,
                    sm.match_name, sm.id as sub_match_id,
                    m.match_url
                FROM throws t
                JOIN legs l ON t.leg_id = l.id
                JOIN sub_matches sm ON l.sub_match_id = sm.id
                JOIN matches m ON sm.match_id = m.id
                WHERE t.remaining_score = 0 AND t.score < 0
            """
            if limit:
                query += f" LIMIT {limit}"
                
            cursor.execute(query)
            finish_throws = cursor.fetchall()
            
            print(f"📊 Found {len(finish_throws)} finish throws needing fixes")
            
            if not finish_throws:
                print("✅ No finish throws need fixing")
                return
            
            successful = 0
            failed = 0
            processed_matches = {}  # Track processed match URLs to avoid duplicate API calls
            
            for i, (throw_id, old_score, old_darts, team_number, round_number, 
                   leg_number, leg_id, match_name, sub_match_id, match_url) in enumerate(finish_throws, 1):
                
                print(f"\\n[{i}/{len(finish_throws)}] Fixing finish in {match_name}, Leg {leg_number}...")
                
                # Skip if we already processed this match
                cache_key = f"{match_url}#{match_name}"
                if cache_key not in processed_matches:
                    corrected_finishes = self.get_corrected_finishes_from_api(match_url, match_name)
                    processed_matches[cache_key] = corrected_finishes
                else:
                    corrected_finishes = processed_matches[cache_key]
                
                # Find the matching finish
                matching_finish = None
                for finish in corrected_finishes:
                    if (finish['leg_number'] == leg_number and 
                        finish['team_number'] == team_number and 
                        finish['round_number'] == round_number):
                        matching_finish = finish
                        break
                
                if matching_finish:
                    new_score = matching_finish['score']
                    new_darts = matching_finish['darts_used']
                    
                    # Update the throw
                    cursor.execute(
                        "UPDATE throws SET score = ?, darts_used = ? WHERE id = ?",
                        (new_score, new_darts, throw_id)
                    )
                    successful += 1
                    print(f"✅ Updated: {old_score} → {new_score} points ({new_darts} darts)")
                else:
                    failed += 1
                    print(f"❌ Could not find matching finish")
                
                # Progress update
                if i % 10 == 0:
                    print(f"\\n📊 Progress: {i}/{len(finish_throws)}")
                    print(f"   ✅ Successful: {successful}")
                    print(f"   ❌ Failed: {failed}")
                    
                    # Commit progress
                    conn.commit()
            
            # Final commit
            conn.commit()
            
            print(f"\\n🎉 Finish score fixing completed!")
            print(f"📊 Final statistics: {successful} successful, {failed} failed")

def main():
    limit = None
    if len(sys.argv) > 1:
        try:
            limit = int(sys.argv[1])
            print(f"🔧 Processing first {limit} finish throws only")
        except ValueError:
            print("Usage: python fix_finish_scores.py [limit]")
            sys.exit(1)
    
    fixer = FinishScoreFixer()
    fixer.fix_all_finish_scores(limit)

if __name__ == "__main__":
    main()