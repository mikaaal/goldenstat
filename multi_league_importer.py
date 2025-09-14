#!/usr/bin/env python3
"""
Multi-League Importer for GoldenStat
Imports match data from multiple N01 Darts leagues for the 2025/2026 season
"""
import asyncio
import time
import requests
from typing import List, Dict, Optional
from datetime import datetime
from new_format_importer import NewFormatImporter


class MultiLeagueImporter:
    def __init__(self, db_path: str = "goldenstat.db"):
        self.importer = NewFormatImporter(db_path)
        self.leagues = {
            # 2025/2026 season leagues
            "Liga A": "https://n01darts.com/n01/league/season.php?id=t_OFlR_9185",
            "Liga B": "https://n01darts.com/n01/league/season.php?id=t_Y2RR_6468", 
            "Liga C": "https://n01darts.com/n01/league/season.php?id=t_jM8s_0341",
            "Liga D": "https://n01darts.com/n01/league/season.php?id=t_Wjxm_8120",
            "Liga E": "https://n01darts.com/n01/league/season.php?id=t_5L4C_6247",
            "Liga F": "https://n01darts.com/n01/league/season.php?id=t_3VAf_1770",
            "Liga G": "https://n01darts.com/n01/league/season.php?id=t_NcAX_0028",
            "Liga H": "https://n01darts.com/n01/league/season.php?id=t_xo0C_7058",
            "Liga I": "https://n01darts.com/n01/league/season.php?id=t_fWIc_3015",
            "Liga J": "https://n01darts.com/n01/league/season.php?id=t_XtZU_4873",
            "Liga K": "https://n01darts.com/n01/league/season.php?id=t_4epA_9547",
            "Liga L": "https://n01darts.com/n01/league/season.php?id=t_v6Vw_6773",
            "Liga M": "https://n01darts.com/n01/league/season.php?id=t_bmWG_5842",
            "Liga N": "https://n01darts.com/n01/league/season.php?id=t_UGYN_2596",
            "Liga O": "https://n01darts.com/n01/league/season.php?id=t_JIvx_1896",
            "Liga P": "https://n01darts.com/n01/league/season.php?id=t_rqTc_6259",
            "Liga Q": "https://n01darts.com/n01/league/season.php?id=t_RY0l_0196"
        }
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })

    def extract_league_id(self, league_url: str) -> Optional[str]:
        """Extract league ID from URL for API calls"""
        try:
            if "id=" in league_url:
                return league_url.split("id=")[1].split("&")[0]
        except Exception as e:
            print(f"❌ Error extracting league ID from {league_url}: {e}")
        return None

    def get_league_matches(self, league_url: str, league_name: str) -> List[str]:
        """Get all match URLs from a league page"""
        print(f"🔍 Scanning {league_name} ({league_url})")
        
        league_id = self.extract_league_id(league_url)
        if not league_id:
            print(f"❌ Could not extract league ID from {league_url}")
            return []

        try:
            # Try to get match list from league API
            api_url = f"https://n01darts.com/n01/api/league/matches.php?league_id={league_id}"
            response = self.session.get(api_url, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                match_urls = []
                
                # Extract match URLs from API response
                for match in data:
                    match_id = match.get('id') or match.get('match_id')
                    if match_id:
                        # Construct match URL
                        match_url = f"https://n01darts.com/n01/api/match/data.php?mid={match_id}"
                        match_urls.append(match_url)
                
                print(f"✅ Found {len(match_urls)} matches in {league_name}")
                return match_urls
                
        except Exception as e:
            print(f"❌ Error getting matches from {league_name}: {e}")

        return []

    def process_match_with_league_info(self, match_url: str, league_name: str) -> bool:
        """Process a match from URL and import with league information"""
        print(f"🎯 Processing match from {match_url} for {league_name}")
        
        match_data = self.importer.fetch_match_data(match_url)
        if not match_data:
            return False
        
        # Extract match information
        match_info = self.importer.extract_match_from_new_format(match_data)
        if not match_info:
            return False
        
        # Get match date from API
        match_date = self.importer.extract_match_date_from_api(match_data)
        if match_date:
            match_info['match_date'] = match_date
        
        # Add league information
        match_info['season'] = '2025/2026'
        match_info['division'] = league_name
        
        try:
            # Import into database with league info
            match_id = self.importer.db.insert_match({
                'team1_name': match_info['team1']['name'],
                'team2_name': match_info['team2']['name'],
                'team1_legs': match_info['team1_legs'],
                'team2_legs': match_info['team2_legs'],
                'team1_avg': match_info.get('team1_avg'),
                'team2_avg': match_info.get('team2_avg'),
                'match_date': match_info.get('match_date'),
                'match_url': match_url,
                'season': match_info.get('season'),
                'division': match_info.get('division')
            })
            
            # Process sub-matches
            for sub_match_info in match_info['sub_matches']:
                self.importer.import_sub_match(match_id, sub_match_info, match_url)
            
            print(f"✅ Successfully imported match {match_id} for {league_name}")
            return True
            
        except Exception as e:
            print(f"❌ Error importing match for {league_name}: {e}")
            return False

    def import_league_matches(self, league_name: str, league_url: str, delay_between_matches: float = 2.0) -> Dict:
        """Import all matches from a specific league"""
        print(f"\n🎯 Starting import for {league_name}")
        
        match_urls = self.get_league_matches(league_url, league_name)
        if not match_urls:
            return {"success": 0, "failed": 0, "total": 0}
        
        success_count = 0
        failed_count = 0
        
        for i, match_url in enumerate(match_urls, 1):
            print(f"📊 Processing match {i}/{len(match_urls)} from {league_name}")
            
            try:
                success = self.process_match_with_league_info(match_url, league_name)
                if success:
                    success_count += 1
                    print(f"✅ Match {i} imported successfully")
                else:
                    failed_count += 1
                    print(f"❌ Failed to import match {i}")
                    
            except Exception as e:
                failed_count += 1
                print(f"❌ Error processing match {i}: {e}")
            
            # Add delay between matches to be respectful to the server
            if i < len(match_urls):  # Don't delay after the last match
                time.sleep(delay_between_matches)
        
        print(f"\n📈 {league_name} import completed:")
        print(f"   ✅ Success: {success_count}")
        print(f"   ❌ Failed: {failed_count}")
        print(f"   📊 Total: {len(match_urls)}")
        
        return {
            "success": success_count,
            "failed": failed_count,
            "total": len(match_urls)
        }

    def import_all_leagues(self, delay_between_leagues: float = 5.0, delay_between_matches: float = 2.0) -> Dict:
        """Import matches from all configured leagues"""
        print("🚀 Starting multi-league import for 2025/2026 season")
        print(f"📋 Configured leagues: {len(self.leagues)}")
        
        total_stats = {"success": 0, "failed": 0, "total": 0}
        league_results = {}
        
        for league_name, league_url in self.leagues.items():
            try:
                stats = self.import_league_matches(league_name, league_url, delay_between_matches)
                league_results[league_name] = stats
                
                # Update totals
                total_stats["success"] += stats["success"]
                total_stats["failed"] += stats["failed"]
                total_stats["total"] += stats["total"]
                
            except Exception as e:
                print(f"❌ Critical error importing {league_name}: {e}")
                league_results[league_name] = {"success": 0, "failed": 0, "total": 0, "error": str(e)}
            
            # Delay between leagues
            if league_name != list(self.leagues.keys())[-1]:  # Don't delay after last league
                print(f"⏱️  Waiting {delay_between_leagues}s before next league...")
                time.sleep(delay_between_leagues)
        
        # Print final summary
        self.print_final_summary(total_stats, league_results)
        
        return {
            "total_stats": total_stats,
            "league_results": league_results
        }

    def print_final_summary(self, total_stats: Dict, league_results: Dict):
        """Print a comprehensive summary of the import process"""
        print("\n" + "="*60)
        print("🎯 MULTI-LEAGUE IMPORT SUMMARY")
        print("="*60)
        print(f"📅 Season: 2025/2026")
        print(f"🕐 Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"\n📊 TOTALS:")
        print(f"   ✅ Successful imports: {total_stats['success']}")
        print(f"   ❌ Failed imports: {total_stats['failed']}")
        print(f"   📋 Total matches processed: {total_stats['total']}")
        
        if total_stats['total'] > 0:
            success_rate = (total_stats['success'] / total_stats['total']) * 100
            print(f"   📈 Success rate: {success_rate:.1f}%")
        
        print(f"\n📋 LEAGUE BREAKDOWN:")
        for league_name, stats in league_results.items():
            if 'error' in stats:
                print(f"   ❌ {league_name}: ERROR - {stats['error']}")
            else:
                print(f"   📊 {league_name}: {stats['success']}/{stats['total']} matches")
        
        print("="*60)

    def import_specific_leagues(self, league_names: List[str], **kwargs) -> Dict:
        """Import matches from specific leagues only"""
        filtered_leagues = {name: url for name, url in self.leagues.items() if name in league_names}
        
        if not filtered_leagues:
            print(f"❌ No matching leagues found for: {league_names}")
            return {"total_stats": {"success": 0, "failed": 0, "total": 0}, "league_results": {}}
        
        print(f"🎯 Importing from {len(filtered_leagues)} specific leagues")
        
        # Temporarily replace leagues dict
        original_leagues = self.leagues
        self.leagues = filtered_leagues
        
        try:
            result = self.import_all_leagues(**kwargs)
        finally:
            # Restore original leagues dict
            self.leagues = original_leagues
        
        return result


def main():
    """Main execution function"""
    print("🎯 GoldenStat Multi-League Importer")
    print("=" * 50)
    
    importer = MultiLeagueImporter()
    
    # You can choose to import all leagues or specific ones:
    
    # Option 1: Import all leagues
    # result = importer.import_all_leagues(delay_between_leagues=5.0, delay_between_matches=2.0)
    
    # Option 2: Import specific leagues (example)
    # result = importer.import_specific_leagues(["Liga A", "Liga B"], delay_between_leagues=3.0)
    
    # Option 3: Import just one league for testing
    result = importer.import_specific_leagues(["Liga A"], delay_between_leagues=0.0, delay_between_matches=1.0)
    
    return result


if __name__ == "__main__":
    result = main()