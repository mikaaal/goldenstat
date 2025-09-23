#!/usr/bin/env python3
"""
Mapping Applier
Applies confirmed player mappings to the raw data in sub_match_participants

Created: 2025-09-21
"""
import sqlite3
import sys
from collections import defaultdict

class MappingApplier:
    def __init__(self, db_path="goldenstat.db"):
        self.db_path = db_path
    
    def get_all_confirmed_mappings(self):
        """Get all confirmed mappings"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT 
                    pm.id as mapping_id,
                    pm.source_player_id,
                    pm.target_player_id,
                    ps.name as source_name,
                    pt.name as target_name,
                    pm.canonical_name,
                    pm.mapping_type
                FROM player_mappings pm
                JOIN players ps ON pm.source_player_id = ps.id
                JOIN players pt ON pm.target_player_id = pt.id
                WHERE pm.status = 'confirmed'
                ORDER BY pm.id
            """)
            
            return [dict(row) for row in cursor.fetchall()]
    
    def apply_mappings_to_sub_matches(self, dry_run=True):
        """Apply all confirmed mappings to sub_match_participants"""
        mappings = self.get_all_confirmed_mappings()
        
        if not mappings:
            print("📭 No confirmed mappings to apply!")
            return 0
        
        print(f"🔧 {'DRY RUN - Would apply' if dry_run else 'Applying'} {len(mappings)} confirmed mappings to sub_match_participants...")
        
        total_updated = 0
        mapping_updates = defaultdict(int)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            for mapping in mappings:
                source_id = mapping['source_player_id']
                target_id = mapping['target_player_id']
                source_name = mapping['source_name']
                target_name = mapping['target_name']
                
                # Count affected sub_match_participants
                cursor.execute("""
                    SELECT COUNT(*) FROM sub_match_participants 
                    WHERE player_id = ?
                """, (source_id,))
                
                affected_count = cursor.fetchone()[0]
                
                if affected_count == 0:
                    continue
                
                print(f"   {'Would update' if dry_run else 'Updating'} {affected_count} records: '{source_name}' → '{target_name}'")
                
                if not dry_run:
                    # Apply the mapping
                    cursor.execute("""
                        UPDATE sub_match_participants 
                        SET player_id = ?
                        WHERE player_id = ?
                    """, (target_id, source_id))
                    
                    actual_updated = cursor.rowcount
                    total_updated += actual_updated
                    mapping_updates[mapping['mapping_type']] += actual_updated
                    
                    if actual_updated != affected_count:
                        print(f"     ⚠️  Expected {affected_count}, actually updated {actual_updated}")
                else:
                    total_updated += affected_count
                    mapping_updates[mapping['mapping_type']] += affected_count
            
            if not dry_run:
                conn.commit()
        
        print(f"\n📊 Summary:")
        print(f"   {'Would update' if dry_run else 'Updated'}: {total_updated} sub_match_participants")
        print(f"   Mappings applied: {len([m for m in mappings if self.count_affected_records(m['source_player_id']) > 0])}")
        
        print(f"\n📋 By mapping type:")
        for mapping_type, count in mapping_updates.items():
            print(f"   {mapping_type}: {count} updates")
        
        return total_updated
    
    def count_affected_records(self, source_player_id):
        """Count how many records would be affected by a mapping"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM sub_match_participants WHERE player_id = ?", (source_player_id,))
            return cursor.fetchone()[0]
    
    def cleanup_unused_players(self, dry_run=True):
        """Remove players that have no sub_match_participants after mappings"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Find players with no sub_match_participants
            cursor.execute("""
                SELECT p.id, p.name
                FROM players p
                WHERE NOT EXISTS (
                    SELECT 1 FROM sub_match_participants smp 
                    WHERE smp.player_id = p.id
                )
                AND p.name NOT LIKE '% %'  -- Only single names (that were probably mapped)
                ORDER BY p.name
            """)
            
            unused_players = [dict(row) for row in cursor.fetchall()]
            
            if not unused_players:
                print("✅ No unused players found!")
                return 0
            
            print(f"🗑️  {'Would remove' if dry_run else 'Removing'} {len(unused_players)} unused players:")
            
            removed_count = 0
            for player in unused_players:
                print(f"   {'Would remove' if dry_run else 'Removing'}: '{player['name']}' (ID: {player['id']})")
                
                if not dry_run:
                    cursor.execute("DELETE FROM players WHERE id = ?", (player['id'],))
                    if cursor.rowcount > 0:
                        removed_count += 1
            
            if not dry_run:
                conn.commit()
                print(f"\n✅ Removed {removed_count} unused players")
            else:
                print(f"\n💡 Use --force to actually remove {len(unused_players)} unused players")
            
            return len(unused_players) if dry_run else removed_count
    
    def verify_mappings_applied(self):
        """Verify that all mappings have been applied correctly"""
        mappings = self.get_all_confirmed_mappings()
        
        print(f"🔍 Verifying {len(mappings)} mappings have been applied...")
        
        issues_found = 0
        
        for mapping in mappings:
            source_id = mapping['source_player_id']
            remaining_count = self.count_affected_records(source_id)
            
            if remaining_count > 0:
                print(f"   ❌ Mapping not fully applied: '{mapping['source_name']}' still has {remaining_count} records")
                issues_found += 1
        
        if issues_found == 0:
            print("✅ All mappings have been applied correctly!")
        else:
            print(f"⚠️  Found {issues_found} mappings that were not fully applied")
        
        return issues_found
    
    def check_specific_sub_match(self, sub_match_id):
        """Check a specific sub_match after applying mappings"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT 
                    sm.id as sub_match_id,
                    sm.match_id,
                    m.match_date,
                    t1.name as team1,
                    t2.name as team2,
                    smp.team_number,
                    p.name as player_name,
                    p.id as player_id
                FROM sub_matches sm
                JOIN matches m ON sm.match_id = m.id
                JOIN teams t1 ON m.team1_id = t1.id
                JOIN teams t2 ON m.team2_id = t2.id
                JOIN sub_match_participants smp ON sm.id = smp.sub_match_id
                JOIN players p ON smp.player_id = p.id
                WHERE sm.id = ?
                ORDER BY smp.team_number, p.name
            """, (sub_match_id,))
            
            results = [dict(row) for row in cursor.fetchall()]
            
            if not results:
                print(f"❌ Sub_match_id {sub_match_id} not found")
                return
            
            print(f"🔍 Sub_match_id {sub_match_id}:")
            print(f"   Date: {results[0]['match_date']}")
            print(f"   Teams: {results[0]['team1']} vs {results[0]['team2']}")
            print(f"   Players:")
            
            for result in results:
                team_name = result['team1'] if result['team_number'] == 1 else result['team2']
                print(f"     Team {result['team_number']} ({team_name}): {result['player_name']} (ID: {result['player_id']})")

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 mapping_applier.py <command> [args...]")
        print("")
        print("Commands:")
        print("  apply [--force]                  - Apply all confirmed mappings to raw data")
        print("  verify                           - Verify mappings have been applied")
        print("  cleanup [--force]                - Remove unused players after mappings")
        print("  check <sub_match_id>             - Check specific sub_match after mappings")
        print("  full-process [--force]           - Apply mappings, cleanup, and verify")
        print("")
        print("Examples:")
        print("  python3 mapping_applier.py apply")
        print("  python3 mapping_applier.py apply --force")
        print("  python3 mapping_applier.py check 9020")
        print("  python3 mapping_applier.py full-process --force")
        return 1
    
    applier = MappingApplier()
    command = sys.argv[1]
    force = "--force" in sys.argv
    
    if command == "apply":
        updated_count = applier.apply_mappings_to_sub_matches(dry_run=not force)
        if not force:
            print(f"\n💡 Use --force to actually apply mappings to {updated_count} records")
    
    elif command == "verify":
        applier.verify_mappings_applied()
    
    elif command == "cleanup":
        removed_count = applier.cleanup_unused_players(dry_run=not force)
        if not force and removed_count > 0:
            print(f"\n💡 Use --force to actually remove {removed_count} unused players")
    
    elif command == "check":
        if len(sys.argv) < 3:
            print("Usage: check <sub_match_id>")
            return 1
        sub_match_id = int(sys.argv[2])
        applier.check_specific_sub_match(sub_match_id)
    
    elif command == "full-process":
        print("🚀 Running full mapping application process...\n")
        
        # Step 1: Apply mappings
        print("Step 1: Applying mappings...")
        updated_count = applier.apply_mappings_to_sub_matches(dry_run=not force)
        print()
        
        # Step 2: Cleanup unused players
        print("Step 2: Cleaning up unused players...")
        removed_count = applier.cleanup_unused_players(dry_run=not force)
        print()
        
        # Step 3: Verify
        print("Step 3: Verifying application...")
        issues = applier.verify_mappings_applied()
        print()
        
        if force:
            print(f"🎉 Process complete!")
            print(f"   Updated: {updated_count} sub_match_participants")
            print(f"   Removed: {removed_count} unused players")
            print(f"   Issues: {issues}")
        else:
            print(f"🔍 DRY RUN complete!")
            print(f"   Would update: {updated_count} sub_match_participants")
            print(f"   Would remove: {removed_count} unused players")
            print(f"\n💡 Use --force to actually execute the full process")
    
    else:
        print(f"Unknown command: {command}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())