#!/usr/bin/env python3
"""
Apply Marcus Gavander case variation mapping
"""
import sqlite3

def apply_marcus_mapping():
    """Apply the Marcus gavander -> Marcus Gavander mapping"""

    source_player_id = 1798  # Marcus gavander
    target_player_id = 278   # Marcus Gavander
    canonical_name = "Marcus Gavander"

    with sqlite3.connect("../goldenstat.db") as conn:
        cursor = conn.cursor()

        # Get all sub-matches for the source player
        cursor.execute("""
            SELECT DISTINCT smp.sub_match_id
            FROM sub_match_participants smp
            WHERE smp.player_id = ?
        """, (source_player_id,))

        sub_matches = cursor.fetchall()

        print(f"Found {len(sub_matches)} sub-matches for Marcus gavander (ID: {source_player_id})")

        # Apply mapping to each sub-match
        for sub_match in sub_matches:
            cursor.execute("""
                INSERT OR REPLACE INTO sub_match_player_mappings (
                    sub_match_id,
                    original_player_id,
                    correct_player_id,
                    correct_player_name,
                    match_context,
                    confidence,
                    mapping_reason,
                    notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                sub_match[0],
                source_player_id,
                target_player_id,
                canonical_name,
                "Case variation mapping - Dartanjang",
                95,
                "Case variation of same player name",
                "Safe temporal validation: same club, different periods"
            ))

        conn.commit()
        print(f"✓ Applied {len(sub_matches)} mappings successfully!")

        # Verify the mapping
        cursor.execute("""
            SELECT COUNT(*)
            FROM sub_match_player_mappings
            WHERE original_player_id = ? AND correct_player_id = ?
        """, (source_player_id, target_player_id))

        count = cursor.fetchone()[0]
        print(f"✓ Verified: {count} mappings in database")

if __name__ == "__main__":
    print("=== Applying Marcus Gavander Case Variation Mapping ===")
    apply_marcus_mapping()
    print("✓ Marcus gavander -> Marcus Gavander mapping completed!")