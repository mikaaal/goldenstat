#!/usr/bin/env python3
"""
Script to clean up duplicate sub_matches that have the same mid (source match ID)
"""
import sqlite3
from typing import List, Tuple

def cleanup_mid_duplicates(db_path: str = "goldenstat.db"):
    """Remove duplicate sub_matches that have the same mid within the same match"""
    
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        
        print("🔍 Finding sub_matches with duplicate mid values...")
        
        # Find sub_matches with same match_id and mid
        cursor.execute("""
            SELECT match_id, mid, COUNT(*) as count, GROUP_CONCAT(id) as ids
            FROM sub_matches 
            WHERE mid IS NOT NULL AND mid != ''
            GROUP BY match_id, mid
            HAVING COUNT(*) > 1
            ORDER BY count DESC
        """)
        
        mid_dupes = cursor.fetchall()
        print(f"Found {len(mid_dupes)} groups of sub_matches with duplicate mid values")
        
        total_removed = 0
        for match_id, mid, count, ids_str in mid_dupes:
            ids = [int(x) for x in ids_str.split(',')]
            keep_id = ids[0]  # Keep the first one
            remove_ids = ids[1:]  # Remove the rest
            
            print(f"\\nMatch {match_id}, mid '{mid}': {count} duplicates")
            print(f"  Keeping sub_match_id {keep_id}, removing: {remove_ids}")
            
            # Show what we're removing
            for remove_id in remove_ids:
                cursor.execute("""
                    SELECT match_type, match_name FROM sub_matches WHERE id = ?
                """, (remove_id,))
                result = cursor.fetchone()
                if result:
                    print(f"    Removing: {result[0]} - {result[1]} (id: {remove_id})")
            
            # Remove participants for duplicate sub_matches
            if remove_ids:
                placeholders = ','.join('?' * len(remove_ids))
                cursor.execute(f"""
                    DELETE FROM sub_match_participants 
                    WHERE sub_match_id IN ({placeholders})
                """, remove_ids)
                participants_removed = cursor.rowcount
                
                # Remove legs for duplicate sub_matches
                cursor.execute(f"""
                    DELETE FROM legs 
                    WHERE sub_match_id IN ({placeholders})
                """, remove_ids)
                legs_removed = cursor.rowcount
                
                # Remove the duplicate sub_matches
                cursor.execute(f"""
                    DELETE FROM sub_matches 
                    WHERE id IN ({placeholders})
                """, remove_ids)
                submatches_removed = cursor.rowcount
                
                print(f"    Removed: {submatches_removed} sub_matches, {participants_removed} participants, {legs_removed} legs")
                total_removed += submatches_removed
        
        print(f"\\n✅ Total sub_matches removed: {total_removed}")
        
        # Verify no more mid duplicates exist
        cursor.execute("""
            SELECT COUNT(*) FROM (
                SELECT match_id, mid, COUNT(*) as count
                FROM sub_matches 
                WHERE mid IS NOT NULL AND mid != ''
                GROUP BY match_id, mid
                HAVING COUNT(*) > 1
            )
        """)
        remaining_mid_dupes = cursor.fetchone()[0]
        
        print(f"\\n📊 Verification:")
        print(f"  Remaining mid duplicates: {remaining_mid_dupes}")
        
        if remaining_mid_dupes == 0:
            print("🎉 All mid-based duplicates successfully removed!")
        else:
            print("⚠️  Some mid duplicates may still remain")
        
        conn.commit()

if __name__ == "__main__":
    cleanup_mid_duplicates()