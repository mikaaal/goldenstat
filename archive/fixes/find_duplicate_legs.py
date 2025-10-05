import sqlite3
import hashlib

conn = sqlite3.connect('goldenstat.db')
cursor = conn.cursor()

# Find legs with identical throw sequences
# We'll create a hash of all throws for each leg to identify duplicates
query = '''
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
ORDER BY l.sub_match_id, l.leg_number, l.id
'''

rows = cursor.execute(query).fetchall()

# Group by sub_match_id and leg_number to find duplicates
from collections import defaultdict
duplicates = defaultdict(list)

for row in rows:
    leg_id, sub_match_id, leg_number, throw_sequence = row
    # Create a hash of the throw sequence
    throw_hash = hashlib.md5(throw_sequence.encode()).hexdigest()
    key = (sub_match_id, leg_number, throw_hash)
    duplicates[key].append(leg_id)

# Find groups with more than one leg_id (duplicates)
duplicate_groups = {k: v for k, v in duplicates.items() if len(v) > 1}

print(f"Found {len(duplicate_groups)} groups of duplicate legs")
print()

total_duplicates = 0
for (sub_match_id, leg_number, throw_hash), leg_ids in duplicate_groups.items():
    print(f"Sub-match {sub_match_id}, Leg {leg_number}: {len(leg_ids)} copies")
    print(f"  Leg IDs: {leg_ids}")
    print(f"  Keep: {min(leg_ids)} (earliest ID)")
    print(f"  Delete: {leg_ids[1:]} ({len(leg_ids)-1} legs)")
    total_duplicates += len(leg_ids) - 1
    print()

print(f"Total legs to delete: {total_duplicates}")

conn.close()
