"""
Interactive review of typo mappings, 20 at a time.

Usage:
    python review_typos.py          # Review and apply
    python review_typos.py --dry    # Review only, don't apply
"""

import sqlite3
import sys
from find_cup_typos import find_typo_duplicates
from cup_database import CupDatabase


def apply_approved(mappings, db_path='cups.db', dry_run=False):
    """Apply approved mappings to the database."""
    cup_db = CupDatabase(db_path)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    inserted = 0
    updated = 0
    removed = 0

    for m in mappings:
        alias_id = m['alias_player_id']
        canonical_id = m['canonical_player_id']
        alias_name = m['alias_name']
        canonical_name = m['canonical_name']
        reason = m['reason']

        # Insert mapping
        if not dry_run:
            cursor.execute("""
                INSERT OR IGNORE INTO cup_player_mappings
                (alias_player_id, canonical_player_id, alias_name, canonical_name, mapping_reason)
                VALUES (?, ?, ?, ?, ?)
            """, (alias_id, canonical_id, alias_name, canonical_name, reason))
        inserted += 1

        # Update participant_players links
        cursor.execute(
            "SELECT id, participant_id FROM participant_players WHERE player_id = ?",
            (alias_id,))
        alias_links = [dict(row) for row in cursor.fetchall()]

        for link in alias_links:
            pp_id = link['id']
            participant_id = link['participant_id']

            cursor.execute(
                "SELECT id FROM participant_players WHERE participant_id = ? AND player_id = ?",
                (participant_id, canonical_id))
            existing = cursor.fetchone()

            if existing:
                if not dry_run:
                    cursor.execute("DELETE FROM participant_players WHERE id = ?", (pp_id,))
                removed += 1
            else:
                if not dry_run:
                    cursor.execute(
                        "UPDATE participant_players SET player_id = ? WHERE id = ?",
                        (canonical_id, pp_id))
                updated += 1

    if not dry_run:
        conn.commit()

    conn.close()
    return inserted, updated, removed


def main():
    dry_run = '--dry' in sys.argv
    batch_size = 20

    print("Scanning for typo duplicates...")
    mappings = find_typo_duplicates()
    print(f"Found {len(mappings)} proposed mappings\n")

    if not mappings:
        return

    approved = []
    total_batches = (len(mappings) + batch_size - 1) // batch_size

    for batch_num in range(total_batches):
        start = batch_num * batch_size
        end = min(start + batch_size, len(mappings))
        batch = mappings[start:end]

        print(f"\n{'='*70}")
        print(f"  Batch {batch_num + 1}/{total_batches}  (mapping {start+1}-{end} of {len(mappings)})")
        print(f"{'='*70}")
        print(f"{'Nr':>3}  {'Alias':<40} -> {'Canonical':<40} {'a':>4} {'c':>4}")
        print(f"{'':>3}  {'':40}    {'':40} {'(x)':>4} {'(x)':>4}")
        print('-' * 100)

        for i, m in enumerate(batch):
            print(f"{i+1:>3}  {m['alias_name']:<40} -> {m['canonical_name']:<40} {m['alias_count']:>4} {m['canonical_count']:>4}")

        print()
        print("  a = godkänn alla    s = hoppa över alla    q = avsluta")
        print("  Eller ange nummer: 1,3,5 för att godkänna specifika")
        print()

        try:
            choice = input("  Val: ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print("\nAvbryter.")
            break

        if choice == 'q':
            break
        elif choice == 'a':
            approved.extend(batch)
            print(f"  -> Godkände alla {len(batch)} i batchen")
        elif choice == 's' or choice == '':
            print(f"  -> Hoppade över batchen")
        else:
            try:
                nums = [int(x.strip()) for x in choice.split(',')]
                picked = [batch[n - 1] for n in nums if 1 <= n <= len(batch)]
                approved.extend(picked)
                print(f"  -> Godkände {len(picked)} av {len(batch)}")
            except (ValueError, IndexError):
                print("  -> Ogiltigt val, hoppar över batchen")

    print(f"\n{'='*70}")
    print(f"Totalt godkända: {len(approved)} av {len(mappings)}")

    if not approved:
        print("Inget att applicera.")
        return

    if dry_run:
        print("\n[DRY RUN - inga ändringar sparas]")

    inserted, updated, removed = apply_approved(approved, dry_run=dry_run)

    prefix = "[DRY] " if dry_run else ""
    print(f"\n{prefix}Resultat:")
    print(f"  {prefix}Mappningar tillagda: {inserted}")
    print(f"  {prefix}Spelarlänkar uppdaterade: {updated}")
    print(f"  {prefix}Spelarlänkar borttagna (konflikter): {removed}")

    if not dry_run:
        print("\nKlart! Ändringar sparade i databasen.")


if __name__ == '__main__':
    main()
