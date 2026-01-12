#!/usr/bin/env python3
"""
Match URL Generator for GoldenStat
Generates all possible match URLs for a division and saves them to a file
"""
import requests
import json
import sys
from typing import List, Dict
from datetime import datetime

class MatchUrlGenerator:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive'
        })

    def get_scheduled_matches(self, tdid: str) -> List[Dict[str, str]]:
        """Get all scheduled matches with exact team pairings from schedule API"""
        try:
            print(f"Fetching scheduled matches for division {tdid}...")

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

                print(f"Found {len(matches)} scheduled matches")
                return matches
            else:
                print(f"Failed to fetch schedule: {response.status_code}")
                return []

        except Exception as e:
            print(f"Error fetching schedule: {e}")
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

        print(f"Generated {len(match_urls)} match URLs from {len(scheduled_matches)} scheduled matches")
        return match_urls

    def save_urls_to_file(self, tdid: str, output_file: str = None):
        """Generate URLs and save them to a file"""
        if output_file is None:
            output_file = f"{tdid}_match_urls.txt"

        print(f"Generating match URLs for division {tdid}")

        # Generate URLs
        match_urls = self.generate_match_urls(tdid)

        if not match_urls:
            print("No URLs generated")
            return False

        # Save to file
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                # Write header with metadata
                f.write(f"# Match URLs for division {tdid}\n")
                f.write(f"# Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"# Total URLs: {len(match_urls)}\n")
                f.write("#\n")

                # Write URLs, one per line
                for url in match_urls:
                    f.write(f"{url}\n")

            print(f"Successfully saved {len(match_urls)} URLs to {output_file}")
            return True

        except Exception as e:
            print(f"Error saving URLs to file: {e}")
            return False

    def generate_multiple_divisions(self, division_ids: List[str]):
        """Generate URLs for multiple divisions"""
        for tdid in division_ids:
            print(f"\n{'='*60}")
            self.save_urls_to_file(tdid)

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 generate_match_urls.py <division_id> [output_file]")
        print("Example: python3 generate_match_urls.py t_jM8s_0341")
        print("Example: python3 generate_match_urls.py t_jM8s_0341 custom_urls.txt")
        return 1
    
    division_id = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None
    
    generator = MatchUrlGenerator()
    success = generator.save_urls_to_file(division_id, output_file)
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())