#!/usr/bin/env python3
"""
Fix match dates by fetching real dates from API startTime
"""
import requests
import json
import sqlite3
import sys
from datetime import datetime
from typing import Optional

class MatchDateFixer:
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

    def get_real_match_date(self, url: str) -> Optional[datetime]:
        """Get real match date from API startTime"""
        try:
            response = self.session.get(url, timeout=10)
            if response.status_code != 200:
                return None
            
            data = response.json()
            if not data or len(data) == 0:
                return None
            
            # Get startTime from first sub-match
            first_match = data[0]
            start_time = first_match.get('startTime', 0)
            
            if start_time > 0:
                # Convert Unix timestamp to datetime
                return datetime.fromtimestamp(start_time)
            
            return None
            
        except Exception as e:
            print(f"❌ Error fetching date for {url}: {str(e)}")
            return None

    def fix_all_dates(self, limit: Optional[int] = None):
        """Fix all match dates in database"""
        print("🚀 Starting match date fixing...")
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Get all matches that need date fixes (those with 2025-09-10 dates)
            query = """
                SELECT id, match_url, match_date 
                FROM matches 
                WHERE DATE(match_date) IN ('2025-09-10', '2025-09-12')
            """
            if limit:
                query += f" LIMIT {limit}"
                
            cursor.execute(query)
            matches = cursor.fetchall()
            
            print(f"📊 Found {len(matches)} matches needing date fixes")
            
            if not matches:
                print("✅ No matches need date fixing")
                return
            
            successful = 0
            failed = 0
            
            for i, (match_id, match_url, old_date) in enumerate(matches, 1):
                print(f"\n[{i}/{len(matches)}] Fixing match {match_id}...")
                
                real_date = self.get_real_match_date(match_url)
                
                if real_date:
                    # Update match date
                    cursor.execute(
                        "UPDATE matches SET match_date = ? WHERE id = ?",
                        (real_date, match_id)
                    )
                    successful += 1
                    print(f"✅ Updated: {old_date} → {real_date}")
                else:
                    failed += 1
                    print(f"❌ Failed to get real date")
                
                # Progress update
                if i % 10 == 0:
                    print(f"\n📊 Progress: {i}/{len(matches)}")
                    print(f"   ✅ Successful: {successful}")
                    print(f"   ❌ Failed: {failed}")
                    
                    # Commit progress
                    conn.commit()
            
            # Final commit
            conn.commit()
            
            print(f"\n🎉 Date fixing completed!")
            print(f"📊 Final statistics: {successful} successful, {failed} failed")

def main():
    limit = None
    if len(sys.argv) > 1:
        try:
            limit = int(sys.argv[1])
            print(f"🔧 Processing first {limit} matches only")
        except ValueError:
            print("Usage: python fix_match_dates.py [limit]")
            sys.exit(1)
    
    fixer = MatchDateFixer()
    fixer.fix_all_dates(limit)

if __name__ == "__main__":
    main()