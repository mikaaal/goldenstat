#!/usr/bin/env python3
"""
Verify Marcus Gavander case variation mapping
"""
import sqlite3

def verify_marcus_mapping():
    """Verify the Marcus mapping was applied correctly"""

    with sqlite3.connect("../goldenstat.db") as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Check the mapping
        cursor.execute("""
            SELECT COUNT(*) as count
            FROM sub_match_player_mappings
            WHERE original_player_id = 1798 AND correct_player_id = 278
        """, )

        result = cursor.fetchone()
        print(f"Marcus gavander -> Marcus Gavander mappings: {result['count']}")

        # Check individual mappings
        cursor.execute("""
            SELECT
                smpm.sub_match_id,
                smpm.confidence,
                smpm.mapping_reason
            FROM sub_match_player_mappings smpm
            WHERE smpm.original_player_id = 1798
            LIMIT 5
        """)

        mappings = cursor.fetchall()
        print(f"\nFirst 5 mappings:")
        for mapping in mappings:
            print(f"  Sub-match {mapping['sub_match_id']}: confidence {mapping['confidence']}")

        # Check total matches now mapped to Marcus Gavander
        cursor.execute("""
            -- Direct matches for Marcus Gavander
            SELECT COUNT(DISTINCT smp.sub_match_id) as direct_matches
            FROM sub_match_participants smp
            WHERE smp.player_id = 278
            AND smp.sub_match_id NOT IN (
                SELECT smpm.sub_match_id
                FROM sub_match_player_mappings smpm
                WHERE smpm.original_player_id = 278
            )
        """)
        direct_matches = cursor.fetchone()['direct_matches']

        cursor.execute("""
            -- Mapped matches for Marcus Gavander
            SELECT COUNT(DISTINCT smpm.sub_match_id) as mapped_matches
            FROM sub_match_player_mappings smpm
            WHERE smpm.correct_player_id = 278
        """)
        mapped_matches = cursor.fetchone()['mapped_matches']

        total_matches = direct_matches + mapped_matches
        print(f"\nMarcus Gavander total matches:")
        print(f"  Direct matches: {direct_matches}")
        print(f"  Mapped matches: {mapped_matches}")
        print(f"  Total effective matches: {total_matches}")

        return total_matches > 0

if __name__ == "__main__":
    print("=== Verifying Marcus Gavander Mapping ===")
    success = verify_marcus_mapping()
    if success:
        print("\nMapping verification successful!")
    else:
        print("\nMapping verification failed!")