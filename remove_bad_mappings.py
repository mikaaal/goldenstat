#!/usr/bin/env python3
"""
Remove Bad Mappings
Removes all problematic player mappings identified by the validator

Created: 2025-09-21
"""
import sqlite3
import sys
from mapping_validator import MappingValidator

class BadMappingRemover:
    def __init__(self, db_path="goldenstat.db"):
        self.db_path = db_path
        self.validator = MappingValidator(db_path)
    
    def remove_problematic_mappings(self, dry_run=True):
        """Remove all problematic mappings"""
        problematic_mappings = self.validator.validate_all_mappings(show_details=False)
        
        if not problematic_mappings:
            print("✅ No problematic mappings found!")
            return 0
        
        print(f"🗑️  Found {len(problematic_mappings)} problematic mappings")
        
        if dry_run:
            print("🔍 DRY RUN - Would remove these mappings:")
            for pm in problematic_mappings:
                mapping = pm['mapping']
                issues = pm['issues']
                print(f"   ID {mapping['mapping_id']}: {mapping['source_name']} → {mapping['target_name']}")
                print(f"     Issues: {', '.join(issues)}")
            return len(problematic_mappings)
        
        print("⚠️  REMOVING problematic mappings...")
        removed_count = 0
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            for pm in problematic_mappings:
                mapping = pm['mapping']
                mapping_id = mapping['mapping_id']
                
                cursor.execute("DELETE FROM player_mappings WHERE id = ?", (mapping_id,))
                
                if cursor.rowcount > 0:
                    removed_count += 1
                    print(f"   ✅ Removed ID {mapping_id}: {mapping['source_name']} → {mapping['target_name']}")
                else:
                    print(f"   ❌ Failed to remove ID {mapping_id}")
            
            conn.commit()
        
        print(f"\n🎉 Successfully removed {removed_count}/{len(problematic_mappings)} problematic mappings")
        return removed_count
    
    def remove_mappings_to_nonexistent_players(self, dry_run=True):
        """Remove mappings where target player has no match data"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Find mappings to players with no match data
            cursor.execute("""
                SELECT 
                    pm.id as mapping_id,
                    pm.source_player_id,
                    pm.target_player_id,
                    ps.name as source_name,
                    pt.name as target_name
                FROM player_mappings pm
                JOIN players ps ON pm.source_player_id = ps.id
                JOIN players pt ON pm.target_player_id = pt.id
                WHERE pm.status = 'confirmed'
                AND NOT EXISTS (
                    SELECT 1 FROM sub_match_participants smp 
                    WHERE smp.player_id = pm.target_player_id
                )
                ORDER BY pm.id
            """)
            
            bad_mappings = [dict(row) for row in cursor.fetchall()]
            
            if not bad_mappings:
                print("✅ No mappings to non-existent players found!")
                return 0
            
            print(f"🗑️  Found {len(bad_mappings)} mappings to players with no match data")
            
            if dry_run:
                print("🔍 DRY RUN - Would remove these mappings:")
                for mapping in bad_mappings:
                    print(f"   ID {mapping['mapping_id']}: {mapping['source_name']} → {mapping['target_name']}")
                return len(bad_mappings)
            
            print("⚠️  REMOVING mappings to non-existent players...")
            removed_count = 0
            
            for mapping in bad_mappings:
                cursor.execute("DELETE FROM player_mappings WHERE id = ?", (mapping['mapping_id'],))
                
                if cursor.rowcount > 0:
                    removed_count += 1
                    print(f"   ✅ Removed ID {mapping['mapping_id']}: {mapping['source_name']} → {mapping['target_name']}")
                else:
                    print(f"   ❌ Failed to remove ID {mapping['mapping_id']}")
            
            conn.commit()
            
            print(f"\n🎉 Successfully removed {removed_count}/{len(bad_mappings)} mappings to non-existent players")
            return removed_count

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 remove_bad_mappings.py <command> [args...]")
        print("")
        print("Commands:")
        print("  validate            - Show all problematic mappings")
        print("  remove-all [--force] - Remove all problematic mappings")
        print("  remove-nonexistent [--force] - Remove mappings to players with no match data")
        print("")
        print("Examples:")
        print("  python3 remove_bad_mappings.py validate")
        print("  python3 remove_bad_mappings.py remove-all")
        print("  python3 remove_bad_mappings.py remove-all --force")
        print("  python3 remove_bad_mappings.py remove-nonexistent --force")
        return 1
    
    remover = BadMappingRemover()
    command = sys.argv[1]
    force = "--force" in sys.argv
    
    if command == "validate":
        problematic_mappings = remover.validator.validate_all_mappings(show_details=False)
        print(f"\n📊 Summary: {len(problematic_mappings)} problematic mappings found")
    
    elif command == "remove-all":
        removed_count = remover.remove_problematic_mappings(dry_run=not force)
        if not force:
            print(f"\n💡 Use --force to actually remove the {removed_count} problematic mappings")
    
    elif command == "remove-nonexistent":
        removed_count = remover.remove_mappings_to_nonexistent_players(dry_run=not force)
        if not force:
            print(f"\n💡 Use --force to actually remove the {removed_count} mappings to non-existent players")
    
    else:
        print(f"Unknown command: {command}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())