#!/usr/bin/env python3
"""
Remove Invalid Mappings
Removes all invalid mappings except specified ones to keep

Created: 2025-09-21
"""
import sqlite3
import sys
from deep_mapping_validator import DeepMappingValidator

class InvalidMappingRemover:
    def __init__(self, db_path="goldenstat.db"):
        self.db_path = db_path
        self.validator = DeepMappingValidator(db_path)
    
    def get_invalid_mapping_ids(self, exclude_ids=None):
        """Get all invalid mapping IDs"""
        if exclude_ids is None:
            exclude_ids = set()
        
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT 
                    pm.id as mapping_id,
                    pm.source_player_id,
                    pm.target_player_id,
                    pm.canonical_name,
                    pm.mapping_type,
                    pm.confidence,
                    ps.name as source_name,
                    pt.name as target_name
                FROM player_mappings pm
                JOIN players ps ON pm.source_player_id = ps.id
                JOIN players pt ON pm.target_player_id = pt.id
                WHERE pm.status = 'confirmed'
                ORDER BY pm.id
            """)
            
            mappings = [dict(row) for row in cursor.fetchall()]
        
        print(f"🔍 Finding invalid mappings from {len(mappings)} total mappings...")
        
        invalid_ids = []
        valid_count = 0
        
        for i, mapping in enumerate(mappings, 1):
            if i % 100 == 0:
                print(f"   Progress: {i}/{len(mappings)} ({i/len(mappings)*100:.1f}%)")
            
            mapping_id = mapping['mapping_id']
            
            # Skip excluded IDs
            if mapping_id in exclude_ids:
                valid_count += 1
                continue
            
            is_valid, issues, warnings, insights = self.validator.validate_mapping_deeply(mapping)
            
            if not is_valid:
                invalid_ids.append(mapping_id)
            else:
                valid_count += 1
        
        print(f"✅ Found {len(invalid_ids)} invalid mappings (excluding {len(exclude_ids)} kept)")
        print(f"   Valid mappings: {valid_count}")
        
        return invalid_ids
    
    def remove_invalid_mappings(self, exclude_ids=None, dry_run=True):
        """Remove all invalid mappings except excluded ones"""
        invalid_ids = self.get_invalid_mapping_ids(exclude_ids)
        
        if not invalid_ids:
            print("✅ No invalid mappings to remove!")
            return 0
        
        print(f"\n{'🔍 DRY RUN - Would remove' if dry_run else '🗑️  REMOVING'} {len(invalid_ids)} invalid mappings")
        
        if exclude_ids:
            print(f"   Keeping {len(exclude_ids)} mappings: {sorted(exclude_ids)}")
        
        if dry_run:
            print(f"   Would remove mapping IDs: {invalid_ids[:10]}{'...' if len(invalid_ids) > 10 else ''}")
            return len(invalid_ids)
        
        removed_count = 0
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Remove in batches for efficiency
            batch_size = 50
            for i in range(0, len(invalid_ids), batch_size):
                batch = invalid_ids[i:i + batch_size]
                placeholders = ','.join(['?' for _ in batch])
                
                cursor.execute(f"""
                    DELETE FROM player_mappings 
                    WHERE id IN ({placeholders})
                """, batch)
                
                removed_count += cursor.rowcount
                
                if (i + batch_size) % 200 == 0 or (i + batch_size) >= len(invalid_ids):
                    print(f"   Removed {removed_count}/{len(invalid_ids)} mappings...")
            
            conn.commit()
        
        print(f"\n🎉 Successfully removed {removed_count}/{len(invalid_ids)} invalid mappings")
        
        # Verify remaining mappings
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM player_mappings WHERE status = 'confirmed'")
            remaining = cursor.fetchone()[0]
            print(f"   Remaining confirmed mappings: {remaining}")
        
        return removed_count

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 remove_invalid_mappings.py <command> [args...]")
        print("")
        print("Commands:")
        print("  remove [--keep id1,id2,...] [--force] - Remove all invalid mappings")
        print("  list [--keep id1,id2,...]              - List invalid mappings that would be removed")
        print("")
        print("Examples:")
        print("  python3 remove_invalid_mappings.py list")
        print("  python3 remove_invalid_mappings.py remove --keep 62,90")
        print("  python3 remove_invalid_mappings.py remove --keep 62,90 --force")
        return 1
    
    command = sys.argv[1]
    
    # Parse arguments
    exclude_ids = set()
    force = False
    
    for i, arg in enumerate(sys.argv[2:], 2):
        if arg == "--keep" and i + 1 < len(sys.argv):
            try:
                exclude_ids = set(int(x.strip()) for x in sys.argv[i + 1].split(','))
            except ValueError:
                print("❌ Invalid ID format for --keep")
                return 1
        elif arg == "--force":
            force = True
    
    remover = InvalidMappingRemover()
    
    if command == "list":
        invalid_ids = remover.get_invalid_mapping_ids(exclude_ids)
        print(f"\n📋 Invalid mapping IDs that would be removed:")
        print(f"   {invalid_ids[:20]}{'...' if len(invalid_ids) > 20 else ''}")
        print(f"   Total: {len(invalid_ids)} mappings")
        if exclude_ids:
            print(f"   Keeping: {sorted(exclude_ids)}")
    
    elif command == "remove":
        removed_count = remover.remove_invalid_mappings(exclude_ids, dry_run=not force)
        if not force:
            print(f"\n💡 Use --force to actually remove the {removed_count} invalid mappings")
        else:
            print(f"\n✅ Cleanup complete! Removed {removed_count} invalid mappings")
    
    else:
        print(f"Unknown command: {command}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())