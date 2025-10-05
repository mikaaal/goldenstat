#!/usr/bin/env python3
"""
Test API Direct Access
Test what data we get from a single match URL
"""
import requests
import json
from smart_import_handler import SmartPlayerMatcher

def test_single_url():
    """Test a single URL directly"""
    url = "https://tk2-228-23746.vs.sakura.ne.jp/n01/tournament/n01_online_t.php?cmd=get_setdata&tmid=t_jM8s_0341_lg_0_s3n5_TU7N_fQ08"

    print(f"Testing URL: {url}")

    try:
        response = requests.get(url, timeout=10)
        print(f"Status: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print(f"Data type: {type(data)}")
            print(f"Data length: {len(data) if isinstance(data, list) else 'N/A'}")

            # Save to file for inspection
            with open('sample_match_data.json', 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            print("Data saved to sample_match_data.json")

            # Try to extract player names manually
            if isinstance(data, list) and len(data) > 0:
                match_info = data[0]
                print("\nFirst match structure:")
                for key, value in match_info.items():
                    if isinstance(value, (str, int, bool)):
                        print(f"  {key}: {value}")
                    else:
                        print(f"  {key}: {type(value)} (length: {len(value) if hasattr(value, '__len__') else 'N/A'})")

                # Look for team/player information
                if 'team1_players' in match_info:
                    print(f"\nTeam 1 players: {match_info['team1_players']}")
                if 'team2_players' in match_info:
                    print(f"Team 2 players: {match_info['team2_players']}")

                # Test smart matcher on found players
                matcher = SmartPlayerMatcher()
                team1_name = match_info.get('team1_name', 'Unknown Team 1')
                team2_name = match_info.get('team2_name', 'Unknown Team 2')

                print(f"\nTeams: {team1_name} vs {team2_name}")

                if 'team1_players' in match_info:
                    for player in match_info['team1_players']:
                        if player:
                            result = matcher.find_player_match(player, team1_name)
                            print(f"  {player} + {team1_name}")
                            print(f"    -> {result['action']}: {result['player_name']} ({result['confidence']}%)")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_single_url()