#!/usr/bin/env python3
"""
Script to clean up duplicate legs and their associated throws
"""
import sqlite3
from typing import List, Tuple

def cleanup_leg_duplicates(db_path: str = "goldenstat.db"):
    """Remove duplicate legs and their throws"""
    
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        
        print("🧹 Starting leg duplicate cleanup...")
        
        # Find duplicate legs
        cursor.execute("""
            SELECT sub_match_id, leg_number, winner_team, first_player_team, total_rounds, 
                   GROUP_CONCAT(id) as leg_ids, COUNT(*) as count
            FROM legs 
            GROUP BY sub_match_id, leg_number, winner_team, first_player_team, total_rounds
            HAVING COUNT(*) > 1
            ORDER BY sub_match_id, leg_number
        """)
        
        duplicates = cursor.fetchall()
        print(f"Found {len(duplicates)} groups of duplicate legs")
        
        total_legs_removed = 0
        total_throws_removed = 0
        
        for sub_match_id, leg_number, winner_team, first_player_team, total_rounds, leg_ids_str, count in duplicates:
            leg_ids = [int(x) for x in leg_ids_str.split(',')]
            keep_id = leg_ids[0]  # Keep the first (lowest ID)
            remove_ids = leg_ids[1:]  # Remove the rest
            
            print(f"\\nSub-match {sub_match_id}, Leg {leg_number}: {count} duplicates")
            print(f"  Keeping leg_id {keep_id}, removing: {remove_ids}")
            
            if remove_ids:
                # Remove throws for duplicate legs
                placeholders = ','.join('?' * len(remove_ids))
                cursor.execute(f"""
                    DELETE FROM throws 
                    WHERE leg_id IN ({placeholders})
                """, remove_ids)
                throws_removed = cursor.rowcount
                total_throws_removed += throws_removed
                
                # Remove duplicate legs
                cursor.execute(f"""
                    DELETE FROM legs 
                    WHERE id IN ({placeholders})
                """, remove_ids)
                legs_removed = cursor.rowcount
                total_legs_removed += legs_removed
                
                print(f"    Removed: {legs_removed} legs, {throws_removed} throws")
        
        print(f"\\n✅ Total removed: {total_legs_removed} duplicate legs, {total_throws_removed} throws")
        
        # Verify no more duplicates exist
        cursor.execute("""
            SELECT COUNT(*) FROM (
                SELECT sub_match_id, leg_number, winner_team, first_player_team, total_rounds, COUNT(*) as count
                FROM legs 
                GROUP BY sub_match_id, leg_number, winner_team, first_player_team, total_rounds
                HAVING COUNT(*) > 1
            )
        """)
        remaining_duplicates = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM legs")
        total_legs = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM throws")
        total_throws = cursor.fetchone()[0]
        
        print(f"\\n📊 Final status:")
        print(f"   Total legs: {total_legs}")
        print(f"   Total throws: {total_throws}")
        print(f"   Remaining leg duplicates: {remaining_duplicates}")
        
        if remaining_duplicates == 0:
            print("🎉 All leg duplicates successfully removed!")
        else:
            print("⚠️  Some leg duplicates may still remain")
        
        conn.commit()

if __name__ == "__main__":
    cleanup_leg_duplicates()