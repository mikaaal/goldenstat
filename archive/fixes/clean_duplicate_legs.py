import sqlite3

conn = sqlite3.connect('goldenstat.db')
cursor = conn.cursor()

# Find duplicate legs: same sub_match_id, leg_number, and identical throws
# We'll keep the leg with the lowest ID and delete the rest

query = '''
WITH leg_throws AS (
    SELECT
        l.id as leg_id,
        l.sub_match_id,
        l.leg_number,
        GROUP_CONCAT(
            t.round_number || '|' ||
            t.team_number || '|' ||
            t.score || '|' ||
            t.remaining_score || '|' ||
            COALESCE(t.darts_used, 'NULL'),
            ';'
        ) as throw_sequence
    FROM legs l
    JOIN throws t ON l.id = t.leg_id
    GROUP BY l.id, l.sub_match_id, l.leg_number
),
duplicates AS (
    SELECT
        sub_match_id,
        leg_number,
        throw_sequence,
        GROUP_CONCAT(leg_id) as leg_ids,
        COUNT(*) as dup_count
    FROM leg_throws
    GROUP BY sub_match_id, leg_number, throw_sequence
    HAVING COUNT(*) > 1
)
SELECT
    sub_match_id,
    leg_number,
    leg_ids,
    dup_count
FROM duplicates
ORDER BY sub_match_id, leg_number
'''

duplicates = cursor.execute(query).fetchall()

print(f"Found {len(duplicates)} duplicate leg groups")
print()

# Collect all leg_ids to delete
legs_to_delete = []

for sub_match_id, leg_number, leg_ids_str, dup_count in duplicates:
    leg_ids = [int(x) for x in leg_ids_str.split(',')]
    # Keep the lowest ID, delete the rest
    keep_id = min(leg_ids)
    delete_ids = [lid for lid in leg_ids if lid != keep_id]

    legs_to_delete.extend(delete_ids)

print(f"Total legs to delete: {len(legs_to_delete)}")
print()

if legs_to_delete:
    print("First 20 leg IDs to delete:")
    print(legs_to_delete[:20])
    print()

    # Auto-confirm deletion
    if True:
        # Delete throws first (foreign key constraint)
        print("Deleting throws for duplicate legs...")
        cursor.execute(f"DELETE FROM throws WHERE leg_id IN ({','.join(map(str, legs_to_delete))})")
        print(f"Deleted {cursor.rowcount} throws")

        # Then delete legs
        print("Deleting duplicate legs...")
        cursor.execute(f"DELETE FROM legs WHERE id IN ({','.join(map(str, legs_to_delete))})")
        print(f"Deleted {cursor.rowcount} legs")

        conn.commit()
        print("Done!")
    else:
        print("Aborted.")

conn.close()
