#!/usr/bin/env python3
"""
Konsolidera case-variationer i players-tabellen för korrekt kapitalisering
"""
import sqlite3
from database import DartDatabase

def consolidate_case_variations():
    """Konsolidera alla case-variationer till normaliserade versioner"""
    print("=== KONSOLIDERAR CASE-VARIATIONER ===")

    db = DartDatabase()
    with sqlite3.connect("goldenstat.db") as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Hitta alla case-variation grupper
        cursor.execute("""
            SELECT
                LOWER(name) as normalized_lower,
                GROUP_CONCAT(id) as player_ids,
                GROUP_CONCAT(name) as player_names,
                COUNT(*) as variation_count
            FROM players
            GROUP BY LOWER(name)
            HAVING COUNT(*) > 1
            ORDER BY variation_count DESC
        """)

        case_groups = cursor.fetchall()
        print(f"Hittade {len(case_groups)} grupper med case-variationer")

        total_consolidations = 0

        for group in case_groups:
            player_ids = list(map(int, group['player_ids'].split(',')))
            player_names = group['player_names'].split(',')

            print(f"\nGrupp: {group['normalized_lower']}")
            for i, (pid, name) in enumerate(zip(player_ids, player_names)):
                print(f"  ID {pid}: \"{name}\"")

            # Bestäm vilken version som ska behållas (normaliserad)
            normalized_name = db.normalize_player_name(player_names[0])

            # Hitta om någon av varianterna redan har det normaliserade namnet
            target_player_id = None
            for pid, name in zip(player_ids, player_names):
                if name == normalized_name:
                    target_player_id = pid
                    break

            # Om ingen har normaliserat namn, uppdatera den första
            if target_player_id is None:
                target_player_id = player_ids[0]
                print(f"  Uppdaterar ID {target_player_id} till: \"{normalized_name}\"")
                cursor.execute(
                    "UPDATE players SET name = ? WHERE id = ?",
                    (normalized_name, target_player_id)
                )
            else:
                print(f"  Behåller ID {target_player_id}: \"{normalized_name}\" (redan korrekt)")

            # Konsolidera alla andra variationer till target_player_id
            other_ids = [pid for pid in player_ids if pid != target_player_id]

            for old_id in other_ids:
                print(f"  Konsoliderar ID {old_id} -> ID {target_player_id}")

                # Uppdatera sub_match_participants
                cursor.execute("""
                    UPDATE sub_match_participants
                    SET player_id = ?
                    WHERE player_id = ?
                """, (target_player_id, old_id))
                participants_updated = cursor.rowcount

                # Hantera sub_match_player_mappings (original_player_id)
                # Om detta skulle skapa samma original och correct ID, ta bort mappningen
                cursor.execute("""
                    DELETE FROM sub_match_player_mappings
                    WHERE original_player_id = ? AND correct_player_id = ?
                """, (old_id, target_player_id))
                mapping_deleted_orig = cursor.rowcount

                cursor.execute("""
                    UPDATE sub_match_player_mappings
                    SET original_player_id = ?
                    WHERE original_player_id = ? AND correct_player_id != ?
                """, (target_player_id, old_id, target_player_id))
                mapping_orig_updated = cursor.rowcount

                # Hantera sub_match_player_mappings (correct_player_id)
                # Om detta skulle skapa samma original och correct ID, ta bort mappningen
                cursor.execute("""
                    DELETE FROM sub_match_player_mappings
                    WHERE correct_player_id = ? AND original_player_id = ?
                """, (old_id, target_player_id))
                mapping_deleted = cursor.rowcount

                cursor.execute("""
                    UPDATE sub_match_player_mappings
                    SET correct_player_id = ?
                    WHERE correct_player_id = ? AND original_player_id != ?
                """, (target_player_id, old_id, target_player_id))
                mapping_corr_updated = cursor.rowcount

                # Ta bort gamla player-posten
                cursor.execute("DELETE FROM players WHERE id = ?", (old_id,))

                print(f"    Uppdaterade: {participants_updated} participants, {mapping_orig_updated} mappings (orig), {mapping_corr_updated} mappings (corr)")
                print(f"    Tog bort: {mapping_deleted_orig} mappings (orig->target), {mapping_deleted} mappings (target->corr)")

            total_consolidations += len(other_ids)

        conn.commit()
        print(f"\n[OK] Konsoliderade {total_consolidations} case-variationer")

        # Uppdatera också alla mappningar till normaliserade namn
        print("\n=== UPPDATERAR MAPPING-NAMN ===")
        cursor.execute("""
            UPDATE sub_match_player_mappings
            SET correct_player_name = (
                SELECT name FROM players WHERE id = correct_player_id
            )
            WHERE correct_player_id IS NOT NULL
        """)

        mappings_updated = cursor.rowcount
        conn.commit()
        print(f"Uppdaterade {mappings_updated} mapping-namn till normaliserade versioner")

        # Verifiera resultat
        print("\n=== VERIFIERING ===")
        cursor.execute("""
            SELECT
                LOWER(name) as normalized_lower,
                COUNT(*) as variation_count
            FROM players
            GROUP BY LOWER(name)
            HAVING COUNT(*) > 1
        """)

        remaining_duplicates = cursor.fetchall()
        if remaining_duplicates:
            print(f"VARNING: {len(remaining_duplicates)} case-dubletter finns kvar:")
            for dup in remaining_duplicates:
                print(f"  {dup['normalized_lower']}: {dup['variation_count']} variationer")
        else:
            print("[OK] Inga case-dubletter kvar!")

if __name__ == "__main__":
    consolidate_case_variations()