import sqlite3
import sys
import io

# Fix Windows console encoding issues
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# Define all duplicate player groups: (name, [IDs with match counts])
# Keep ID with most matches
duplicates = [
    ("Ted Öbom", [(298, 47), (1240, 15), (1465, 5)]),  # 3 copies
    ("Alessio Tampella", [(16, 50), (1981, 24)]),
    ("Benny Östlund", [(1117, 42), (1507, 25)]),
    ("Christer Ågren", [(1852, 41), (1320, 4)]),
    ("Gustav Öström", [(362, 29), (1057, 7)]),
    ("Kim Örnfjärd", [(1063, 29), (992, 2)]),
    ("Magda Kuhl", [(281, 30), (2407, 3)]),
    ("Martin Ross-langley", [(20, 13), (1985, 11)]),
    ("Patrik Öbrink", [(1765, 14), (207, 6)]),
    ("Peo Åkergren", [(445, 72), (439, 12)]),
    ("Per Österberg", [(1027, 39), (2008, 28)]),
    ("Ricky Dunér", [(1251, 98), (180, 4)]),
    ("Robert Kaliszczak", [(1999, 22), (1588, 18)]),
    ("Sebastian Caris (Mitt i DC)", [(192, 80), (2331, 0)]),  # Has mappings!
    ("Stefan Ågren", [(910, 34), (2370, 3)])
]

conn = sqlite3.connect('goldenstat.db')
cursor = conn.cursor()

print("Starting automatic merge of 15 duplicate player groups...\n")

for name, id_match_pairs in duplicates:
    # Sort by match count descending to get keep_id first
    sorted_ids = sorted(id_match_pairs, key=lambda x: x[1], reverse=True)
    keep_id = sorted_ids[0][0]
    merge_ids = [id_pair[0] for id_pair in sorted_ids[1:]]

    print(f"=== {name} ===")
    print(f"Keeping ID {keep_id} ({sorted_ids[0][1]} matches)")
    print(f"Merging: {', '.join([f'ID {id_pair[0]} ({id_pair[1]} matches)' for id_pair in sorted_ids[1:]])}")

    for merge_id in merge_ids:
        # Update sub_match_participants
        cursor.execute("""
            UPDATE sub_match_participants
            SET player_id = ?
            WHERE player_id = ?
        """, (keep_id, merge_id))
        updated_participants = cursor.rowcount

        # Handle sub_match_player_mappings
        # Delete mappings where both IDs would become the same (violates CHECK constraint)
        cursor.execute("""
            DELETE FROM sub_match_player_mappings
            WHERE (original_player_id = ? AND correct_player_id = ?)
               OR (original_player_id = ? AND correct_player_id = ?)
        """, (keep_id, merge_id, merge_id, keep_id))
        deleted_mappings = cursor.rowcount

        # Update remaining mappings - original column
        cursor.execute("""
            UPDATE sub_match_player_mappings
            SET original_player_id = ?
            WHERE original_player_id = ?
        """, (keep_id, merge_id))
        updated_mappings_original = cursor.rowcount

        # Update remaining mappings - correct column
        cursor.execute("""
            UPDATE sub_match_player_mappings
            SET correct_player_id = ?
            WHERE correct_player_id = ?
        """, (keep_id, merge_id))
        updated_mappings_correct = cursor.rowcount

        # Delete the merged player
        cursor.execute("DELETE FROM players WHERE id = ?", (merge_id,))

        mapping_msg = f"{updated_mappings_original} mappings (original), {updated_mappings_correct} mappings (correct)"
        if deleted_mappings > 0:
            mapping_msg += f", {deleted_mappings} deleted (would violate constraint)"
        print(f"  Merged ID {merge_id} -> {keep_id}: {updated_participants} participants, {mapping_msg}")

    # Verify final count
    cursor.execute("""
        SELECT COUNT(*)
        FROM sub_match_participants
        WHERE player_id = ?
    """, (keep_id,))
    final_count = cursor.fetchone()[0]
    print(f"  Final: ID {keep_id} now has {final_count} sub-matches\n")

conn.commit()

print("\n=== Verification ===")
print("Checking for remaining duplicates...")
cursor.execute("""
    SELECT name, COUNT(*) as count, GROUP_CONCAT(id) as ids
    FROM players
    GROUP BY name
    HAVING COUNT(*) > 1
    ORDER BY name
""")
remaining = cursor.fetchall()

if remaining:
    print(f"WARNING: {len(remaining)} duplicate names still exist:")
    for row in remaining:
        print(f"  {row[0]}: IDs {row[2]}")
else:
    print("✓ No duplicate names remaining!")

conn.close()
print("\nMerge completed successfully!")
