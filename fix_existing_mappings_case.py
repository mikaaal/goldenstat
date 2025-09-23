#!/usr/bin/env python3
"""
Fix case issues in existing confirmed mappings
"""
import sqlite3

def normalize_to_title_case(name):
    """Convert name to proper title case"""
    words = name.strip().split()
    return ' '.join(word.capitalize() for word in words if word)

def fix_mapping_cases():
    print("🔧 Fixing case issues in existing mappings...")
    
    with sqlite3.connect("goldenstat.db") as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Get all confirmed mappings
        cursor.execute("""
            SELECT id, canonical_name, mapping_type 
            FROM player_mappings 
            WHERE status = 'confirmed'
        """)
        
        mappings = cursor.fetchall()
        
        updates_needed = []
        
        for mapping in mappings:
            original_name = mapping['canonical_name']
            fixed_name = normalize_to_title_case(original_name)
            
            if original_name != fixed_name:
                updates_needed.append({
                    'id': mapping['id'],
                    'original': original_name,
                    'fixed': fixed_name,
                    'mapping_type': mapping['mapping_type']
                })
        
        print(f"📊 Found {len(updates_needed)} mappings that need case fixes:")
        
        if not updates_needed:
            print("   ✅ All mappings already have correct case!")
            return
        
        # Show what will be updated
        for update in updates_needed[:10]:  # Show first 10
            print(f"   '{update['original']}' → '{update['fixed']}'")
        
        if len(updates_needed) > 10:
            print(f"   ... and {len(updates_needed) - 10} more")
        
        # Auto-update for now (skip confirmation in CLI environment)
        print(f"\n🔄 Proceeding with updates...")
        
        # Perform updates
        updated_count = 0
        for update in updates_needed:
            cursor.execute("""
                UPDATE player_mappings 
                SET canonical_name = ?, 
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (update['fixed'], update['id']))
            
            if cursor.rowcount > 0:
                updated_count += 1
                print(f"   ✅ Updated: '{update['original']}' → '{update['fixed']}'")
        
        conn.commit()
        
        print(f"\n🎉 Successfully updated {updated_count} mappings!")

if __name__ == "__main__":
    fix_mapping_cases()