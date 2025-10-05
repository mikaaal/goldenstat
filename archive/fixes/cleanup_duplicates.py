#!/usr/bin/env python3
"""
Script to clean up duplicate entries in the database
"""
import sqlite3
from typing import List, Tuple

def cleanup_duplicates(db_path: str = "goldenstat.db"):
    """Remove duplicate entries from the database"""
    
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        
        print("🧹 Starting duplicate cleanup...")
        
        # 1. Clean up duplicate sub_match_participants
        print("\n📊 Cleaning sub_match_participants...")
        
        # Find duplicates
        cursor.execute("""
            SELECT sub_match_id, player_id, team_number, COUNT(*) as count
            FROM sub_match_participants 
            GROUP BY sub_match_id, player_id, team_number
            HAVING COUNT(*) > 1
        """)
        participant_dupes = cursor.fetchall()
        
        print(f"Found {len(participant_dupes)} duplicate participant groups")
        
        participants_removed = 0
        for sub_match_id, player_id, team_number, count in participant_dupes:
            # Keep the first one, delete the rest
            cursor.execute("""
                DELETE FROM sub_match_participants 
                WHERE id NOT IN (
                    SELECT MIN(id) 
                    FROM sub_match_participants 
                    WHERE sub_match_id = ? AND player_id = ? AND team_number = ?
                ) AND sub_match_id = ? AND player_id = ? AND team_number = ?
            """, (sub_match_id, player_id, team_number, sub_match_id, player_id, team_number))
            participants_removed += count - 1
        
        print(f"✅ Removed {participants_removed} duplicate participant entries")
        
        # 2. Clean up duplicate sub_matches
        print("\n🎯 Cleaning sub_matches...")
        
        # Find duplicates
        cursor.execute("""
            SELECT match_id, match_number, match_type, match_name, COUNT(*) as count
            FROM sub_matches 
            GROUP BY match_id, match_number, match_type, match_name
            HAVING COUNT(*) > 1
        """)
        submatch_dupes = cursor.fetchall()
        
        print(f"Found {len(submatch_dupes)} duplicate sub_match groups")
        
        submatches_removed = 0
        for match_id, match_number, match_type, match_name, count in submatch_dupes:
            # Get all IDs for this duplicate group
            cursor.execute("""
                SELECT id FROM sub_matches 
                WHERE match_id = ? AND match_number = ? AND match_type = ? AND match_name = ?
                ORDER BY id
            """, (match_id, match_number, match_type, match_name))
            
            ids = [row[0] for row in cursor.fetchall()]
            keep_id = ids[0]  # Keep the first one
            delete_ids = ids[1:]  # Delete the rest
            
            if delete_ids:
                # First, delete participants for the duplicate sub_matches
                placeholders = ','.join('?' * len(delete_ids))
                cursor.execute(f"""
                    DELETE FROM sub_match_participants 
                    WHERE sub_match_id IN ({placeholders})
                """, delete_ids)
                
                # Then delete legs for the duplicate sub_matches
                cursor.execute(f"""
                    DELETE FROM legs 
                    WHERE sub_match_id IN ({placeholders})
                """, delete_ids)
                
                # Finally delete the duplicate sub_matches
                cursor.execute(f"""
                    DELETE FROM sub_matches 
                    WHERE id IN ({placeholders})
                """, delete_ids)
                
                submatches_removed += len(delete_ids)
                print(f"  Removed {len(delete_ids)} duplicates for match_id={match_id}, keeping id={keep_id}")
        
        print(f"✅ Removed {submatches_removed} duplicate sub_match entries")
        
        # 3. Check for any remaining orphaned participants
        print("\n🔍 Checking for orphaned participants...")
        cursor.execute("""
            SELECT COUNT(*) FROM sub_match_participants smp
            LEFT JOIN sub_matches sm ON smp.sub_match_id = sm.id
            WHERE sm.id IS NULL
        """)
        orphaned_count = cursor.fetchone()[0]
        
        if orphaned_count > 0:
            print(f"Found {orphaned_count} orphaned participants, removing...")
            cursor.execute("""
                DELETE FROM sub_match_participants 
                WHERE sub_match_id NOT IN (SELECT id FROM sub_matches)
            """)
            print(f"✅ Removed {orphaned_count} orphaned participants")
        else:
            print("✅ No orphaned participants found")
        
        # 4. Final verification
        print("\n📈 Final verification...")
        
        # Check remaining duplicates
        cursor.execute("""
            SELECT COUNT(*) FROM (
                SELECT sub_match_id, player_id, team_number, COUNT(*) as count
                FROM sub_match_participants 
                GROUP BY sub_match_id, player_id, team_number
                HAVING COUNT(*) > 1
            )
        """)
        remaining_participant_dupes = cursor.fetchone()[0]
        
        cursor.execute("""
            SELECT COUNT(*) FROM (
                SELECT match_id, match_number, match_type, match_name, COUNT(*) as count
                FROM sub_matches 
                GROUP BY match_id, match_number, match_type, match_name
                HAVING COUNT(*) > 1
            )
        """)
        remaining_submatch_dupes = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM sub_matches")
        total_submatches = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM sub_match_participants")
        total_participants = cursor.fetchone()[0]
        
        print(f"📊 Database status after cleanup:")
        print(f"   Total sub_matches: {total_submatches}")
        print(f"   Total participants: {total_participants}")
        print(f"   Remaining participant duplicates: {remaining_participant_dupes}")
        print(f"   Remaining sub_match duplicates: {remaining_submatch_dupes}")
        
        if remaining_participant_dupes == 0 and remaining_submatch_dupes == 0:
            print("🎉 All duplicates successfully removed!")
        else:
            print("⚠️  Some duplicates may still remain")
        
        conn.commit()

if __name__ == "__main__":
    cleanup_duplicates()