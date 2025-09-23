#!/usr/bin/env python3
"""
Find potential mappings for players with single letter surnames
"""
import sqlite3
import re
from collections import defaultdict

def find_single_letter_matches():
    print("🔍 Finding potential matches for single letter surnames...")
    
    with sqlite3.connect("goldenstat.db") as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Get all players with single letter surnames (pattern: "Name X")
        cursor.execute("""
            SELECT p.id, p.name, 
                   COUNT(DISTINCT smp.sub_match_id) as matches,
                   GROUP_CONCAT(DISTINCT t.name) as teams,
                   MIN(m.match_date) as first_match,
                   MAX(m.match_date) as last_match
            FROM players p
            LEFT JOIN sub_match_participants smp ON p.id = smp.player_id
            LEFT JOIN sub_matches sm ON smp.sub_match_id = sm.id
            LEFT JOIN matches m ON sm.match_id = m.id
            LEFT JOIN teams t ON t.id = CASE WHEN smp.team_number = 1 THEN m.team1_id ELSE m.team2_id END
            WHERE p.name GLOB '* [A-Öa-ö]'
            GROUP BY p.id, p.name
            HAVING COUNT(DISTINCT smp.sub_match_id) > 0
            ORDER BY p.name
        """)
        
        single_letter_players = [dict(row) for row in cursor.fetchall()]
        
        # Group by first name
        by_first_name = defaultdict(list)
        for player in single_letter_players:
            # Extract first name (everything before the last space)
            parts = player['name'].split()
            if len(parts) >= 2:
                first_name = ' '.join(parts[:-1])  # Everything except last word
                last_part = parts[-1]
                
                # Check if last part is really a single letter
                if len(last_part) == 1:
                    by_first_name[first_name.lower()].append(player)
        
        print(f"Found {len(single_letter_players)} players with single letter surnames")
        print(f"Grouped into {len(by_first_name)} unique first names")
        
        # Now find potential full name matches for each first name
        potential_matches = []
        
        for first_name, players in by_first_name.items():
            if len(players) < 1:
                continue
                
            # Look for players with same first name but full surname
            cursor.execute("""
                SELECT p.id, p.name,
                       COUNT(DISTINCT smp.sub_match_id) as matches,
                       GROUP_CONCAT(DISTINCT t.name) as teams,
                       MIN(m.match_date) as first_match,
                       MAX(m.match_date) as last_match
                FROM players p
                LEFT JOIN sub_match_participants smp ON p.id = smp.player_id
                LEFT JOIN sub_matches sm ON smp.sub_match_id = sm.id
                LEFT JOIN matches m ON sm.match_id = m.id
                LEFT JOIN teams t ON t.id = CASE WHEN smp.team_number = 1 THEN m.team1_id ELSE m.team2_id END
                WHERE LOWER(p.name) LIKE ?
                  AND p.name NOT GLOB '* [A-Öa-ö]'  -- Exclude single letter surnames
                  AND LENGTH(p.name) > LENGTH(?)    -- Must be longer than just first name + space
                GROUP BY p.id, p.name
                HAVING COUNT(DISTINCT smp.sub_match_id) > 0
            """, (f"{first_name} %", first_name + " X"))
            
            full_name_candidates = [dict(row) for row in cursor.fetchall()]
            
            # For each single letter player, check against full name candidates
            for single_player in players:
                single_letter = single_player['name'].split()[-1]
                
                for candidate in full_name_candidates:
                    # Check if the full surname starts with the single letter
                    candidate_parts = candidate['name'].split()
                    if len(candidate_parts) >= 2:
                        candidate_surname = candidate_parts[-1]
                        
                        if candidate_surname.lower().startswith(single_letter.lower()):
                            # Check for team overlap
                            single_teams = set(single_player['teams'].split(',')) if single_player['teams'] else set()
                            candidate_teams = set(candidate['teams'].split(',')) if candidate['teams'] else set()
                            common_teams = single_teams & candidate_teams
                            
                            potential_matches.append({
                                'single_letter_player': single_player,
                                'full_name_player': candidate,
                                'first_name': first_name,
                                'single_letter': single_letter,
                                'full_surname': candidate_surname,
                                'common_teams': list(common_teams),
                                'team_overlap_count': len(common_teams)
                            })
        
        # Sort by team overlap and display results
        potential_matches.sort(key=lambda x: (x['team_overlap_count'], x['first_name']), reverse=True)
        
        print(f"\n📋 Found {len(potential_matches)} potential matches:")
        
        high_confidence = []
        medium_confidence = []
        low_confidence = []
        
        for match in potential_matches:
            single = match['single_letter_player']
            full = match['full_name_player']
            
            print(f"\n🎯 {match['first_name']} {match['single_letter']} ↔ {full['name']}")
            print(f"   Single letter: {single['matches']} matches ({single['first_match']} to {single['last_match']})")
            print(f"   Full name: {full['matches']} matches ({full['first_match']} to {full['last_match']})")
            
            if match['common_teams']:
                print(f"   Common teams: {', '.join(match['common_teams'][:3])}")
                confidence = "HIGH" if match['team_overlap_count'] >= 2 else "MEDIUM"
                if confidence == "HIGH":
                    high_confidence.append(match)
                else:
                    medium_confidence.append(match)
            else:
                print(f"   No common teams")
                confidence = "LOW"
                low_confidence.append(match)
            
            print(f"   Confidence: {confidence}")
        
        print(f"\n📊 Summary:")
        print(f"   High confidence (2+ common teams): {len(high_confidence)}")
        print(f"   Medium confidence (1 common team): {len(medium_confidence)}")
        print(f"   Low confidence (no common teams): {len(low_confidence)}")
        
        return high_confidence, medium_confidence, low_confidence

if __name__ == "__main__":
    high, medium, low = find_single_letter_matches()