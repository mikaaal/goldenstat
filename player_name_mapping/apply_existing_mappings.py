#!/usr/bin/env python3
"""
Apply existing mappings by moving matches from base players to mapped players.
This fixes matches that were imported before mappings were created.
"""
import sqlite3

def remove_duplicate_participants(dry_run=True):
    """
    Remove duplicate participants where both base and mapped player exist in same sub-match.
    Keep only the mapped (correct) player.
    """
    with sqlite3.connect("goldenstat.db") as conn:
        cursor = conn.cursor()

        # Find all cases where both original and correct player exist in same sub-match
        cursor.execute('''
            SELECT DISTINCT
                smpm.sub_match_id,
                smpm.original_player_id,
                smpm.correct_player_id,
                smp.id as participant_id,
                p1.name as original_name,
                p2.name as correct_name
            FROM sub_match_player_mappings smpm
            JOIN sub_match_participants smp ON
                smpm.sub_match_id = smp.sub_match_id AND
                smpm.original_player_id = smp.player_id
            JOIN players p1 ON smpm.original_player_id = p1.id
            JOIN players p2 ON smpm.correct_player_id = p2.id
            -- Check if correct player ALSO exists in this sub-match
            WHERE EXISTS (
                SELECT 1
                FROM sub_match_participants smp2
                WHERE smp2.sub_match_id = smpm.sub_match_id
                AND smp2.player_id = smpm.correct_player_id
                AND smp2.team_number = smp.team_number
            )
            ORDER BY smpm.sub_match_id
        ''')

        duplicates = cursor.fetchall()

        print(f"\n=== Removing {len(duplicates)} duplicate participants ===")

        if duplicates:
            removed_count = 0
            for sub_match_id, orig_id, correct_id, participant_id, orig_name, correct_name in duplicates[:10]:
                print(f"  Sub-match {sub_match_id}: Removing {orig_name} (keeping {correct_name})")

            if len(duplicates) > 10:
                print(f"  ... and {len(duplicates) - 10} more")

            if not dry_run:
                # Delete the original player participants (keep the correct ones)
                participant_ids = [row[3] for row in duplicates]
                placeholders = ','.join('?' * len(participant_ids))
                cursor.execute(f'''
                    DELETE FROM sub_match_participants
                    WHERE id IN ({placeholders})
                ''', participant_ids)

                removed_count = cursor.rowcount
                conn.commit()
                print(f"\nRemoved {removed_count} duplicate participants")
            else:
                print(f"\n[DRY RUN] Would remove {len(duplicates)} duplicate participants")

            return len(duplicates)
        else:
            print("No duplicates found!")
            return 0

def apply_existing_mappings(dry_run=True):
    """
    Apply all existing mappings by updating sub_match_participants.

    For each mapping in sub_match_player_mappings:
    - Update sub_match_participants to use correct_player_id instead of original_player_id
    """
    with sqlite3.connect("goldenstat.db") as conn:
        cursor = conn.cursor()

        # Get all unique mappings (original -> correct player)
        cursor.execute('''
            SELECT DISTINCT
                original_player_id,
                correct_player_id,
                p1.name as original_name,
                p2.name as correct_name,
                COUNT(DISTINCT sub_match_id) as mapping_count
            FROM sub_match_player_mappings smpm
            JOIN players p1 ON smpm.original_player_id = p1.id
            JOIN players p2 ON smpm.correct_player_id = p2.id
            GROUP BY original_player_id, correct_player_id
            ORDER BY mapping_count DESC
        ''')

        mappings = cursor.fetchall()

        print(f"=== Found {len(mappings)} unique player mappings ===\n")

        total_updated = 0

        for orig_id, correct_id, orig_name, correct_name, mapping_count in mappings:
            # Get all sub_match_ids that should be mapped
            cursor.execute('''
                SELECT DISTINCT sub_match_id
                FROM sub_match_player_mappings
                WHERE original_player_id = ? AND correct_player_id = ?
            ''', (orig_id, correct_id))

            sub_match_ids = [row[0] for row in cursor.fetchall()]

            if not sub_match_ids:
                continue

            # Check how many participants currently use the original player
            placeholders = ','.join('?' * len(sub_match_ids))
            cursor.execute(f'''
                SELECT COUNT(*)
                FROM sub_match_participants
                WHERE player_id = ? AND sub_match_id IN ({placeholders})
            ''', [orig_id] + sub_match_ids)

            current_count = cursor.fetchone()[0]

            if current_count == 0:
                print(f"SKIP: {orig_name} -> {correct_name}: Already applied ({mapping_count} mappings)")
                continue

            print(f"UPDATE: {orig_name} (ID {orig_id}) -> {correct_name} (ID {correct_id})")
            print(f"  Will update {current_count} participants across {len(sub_match_ids)} sub-matches")

            if not dry_run:
                # Update all participants to use correct player
                cursor.execute(f'''
                    UPDATE sub_match_participants
                    SET player_id = ?
                    WHERE player_id = ? AND sub_match_id IN ({placeholders})
                ''', [correct_id, orig_id] + sub_match_ids)

                updated = cursor.rowcount
                total_updated += updated
                print(f"  Updated {updated} participants")
            else:
                total_updated += current_count
                print(f"  [DRY RUN] Would update {current_count} participants")

            print()

        if not dry_run:
            conn.commit()
            print(f"\n=== COMPLETED ===")
            print(f"Total participants updated: {total_updated}")
        else:
            print(f"\n=== DRY RUN COMPLETED ===")
            print(f"Would update {total_updated} participants total")
            print(f"\nRun with dry_run=False to apply changes")

def verify_mappings():
    """Verify that mappings have been applied correctly"""
    with sqlite3.connect("goldenstat.db") as conn:
        cursor = conn.cursor()

        print("\n=== VERIFICATION ===\n")

        # Check for remaining unmapped matches
        cursor.execute('''
            SELECT
                p.name,
                p.id,
                COUNT(DISTINCT smp.sub_match_id) as remaining_matches,
                COUNT(DISTINCT smpm.sub_match_id) as mapped_matches
            FROM players p
            JOIN sub_match_participants smp ON p.id = smp.player_id
            LEFT JOIN sub_match_player_mappings smpm ON p.id = smpm.original_player_id
                AND smp.sub_match_id = smpm.sub_match_id
            WHERE smpm.sub_match_id IS NOT NULL
            GROUP BY p.id, p.name
            HAVING remaining_matches > 0
            ORDER BY remaining_matches DESC
            LIMIT 20
        ''')

        remaining = cursor.fetchall()

        if remaining:
            print(f"Players with unmapped matches still in sub_match_participants:")
            for name, pid, remaining_count, mapped_count in remaining:
                print(f"  {name} (ID {pid}): {remaining_count} matches still need mapping")
        else:
            print("All mappings have been applied correctly!")

if __name__ == "__main__":
    import sys

    # Check for --apply flag
    if "--apply" in sys.argv:
        print("APPLYING MAPPINGS (not a dry run)\n")
        print("Step 1: Remove duplicates")
        remove_duplicate_participants(dry_run=False)
        print("\nStep 2: Apply mappings")
        apply_existing_mappings(dry_run=False)
        print("\nStep 3: Verify")
        verify_mappings()
    else:
        print("DRY RUN MODE (no changes will be made)\n")
        print("Run with --apply to actually update the database\n")
        print("Step 1: Remove duplicates")
        remove_duplicate_participants(dry_run=True)
        print("\nStep 2: Apply mappings")
        apply_existing_mappings(dry_run=True)
