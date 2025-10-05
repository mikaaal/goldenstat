#!/usr/bin/env python3
"""
Automatisk mappning av case-variationer
"""
import sqlite3

def fix_case_variations():
    """Fix all unmapped case variations automatically"""
    print("=== AUTOMATISK CASE-VARIATION MAPPNING ===")

    with sqlite3.connect("goldenstat.db") as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Hitta alla omappade case-variationer
        cursor.execute("""
            WITH case_variations AS (
                SELECT
                    p1.id as id1,
                    p1.name as name1,
                    p2.id as id2,
                    p2.name as name2,
                    LOWER(p1.name) as lower_name
                FROM players p1
                JOIN players p2 ON LOWER(p1.name) = LOWER(p2.name) AND p1.id < p2.id
                WHERE p1.name != p2.name
            ),
            mapped_variations AS (
                SELECT DISTINCT
                    original_player_id,
                    correct_player_id
                FROM sub_match_player_mappings
            )
            SELECT cv.*
            FROM case_variations cv
            LEFT JOIN mapped_variations mv ON (
                (cv.id1 = mv.original_player_id AND cv.id2 = mv.correct_player_id)
                OR
                (cv.id2 = mv.original_player_id AND cv.id1 = mv.correct_player_id)
            )
            WHERE mv.original_player_id IS NULL
            ORDER BY cv.lower_name
        """)

        cases = cursor.fetchall()
        print(f"Hittade {len(cases)} omappade case-variationer")

        mappings_created = 0
        for case in cases:
            # Räkna matcher för varje spelare
            cursor.execute('SELECT COUNT(*) as count FROM sub_match_participants WHERE player_id = ?', (case['id1'],))
            matches1 = cursor.fetchone()['count']
            cursor.execute('SELECT COUNT(*) as count FROM sub_match_participants WHERE player_id = ?', (case['id2'],))
            matches2 = cursor.fetchone()['count']

            # Bestäm vem som ska vara "correct" (den med flest matcher)
            if matches1 >= matches2:
                correct_id = case['id1']
                correct_name = case['name1']
                original_id = case['id2']
                original_name = case['name2']
                primary_matches = matches1
                secondary_matches = matches2
            else:
                correct_id = case['id2']
                correct_name = case['name2']
                original_id = case['id1']
                original_name = case['name1']
                primary_matches = matches2
                secondary_matches = matches1

            # Skapa mappning från mindre till större spelare
            if secondary_matches > 0:  # Bara om original har matcher att mappa
                cursor.execute("""
                    INSERT OR IGNORE INTO sub_match_player_mappings (
                        sub_match_id,
                        original_player_id,
                        correct_player_id,
                        correct_player_name,
                        match_context,
                        confidence,
                        mapping_reason,
                        notes
                    )
                    SELECT DISTINCT
                        smp.sub_match_id,
                        ?,
                        ?,
                        ?,
                        'Case variation automatic mapping',
                        99,
                        'Automatic case variation mapping',
                        ?
                    FROM sub_match_participants smp
                    WHERE smp.player_id = ?
                """, (
                    original_id,
                    correct_id,
                    correct_name,
                    f"Mapped '{original_name}' -> '{correct_name}' ({secondary_matches} -> {primary_matches} matches)",
                    original_id
                ))

                mappings_added = cursor.rowcount
                mappings_created += mappings_added

                print(f"  {case['lower_name']}: '{original_name}' -> '{correct_name}' ({mappings_added} mappningar)")

        conn.commit()
        print(f"\n=== SLUTFÖRT ===")
        print(f"Skapade totalt {mappings_created} mappningar för {len(cases)} case-variationer")

def verify_case_mappings():
    """Verify that case mappings worked correctly"""
    print("\n=== VERIFIERING ===")

    with sqlite3.connect("goldenstat.db") as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Kontrollera återstående omappade variationer
        cursor.execute("""
            WITH case_variations AS (
                SELECT
                    p1.id as id1,
                    p1.name as name1,
                    p2.id as id2,
                    p2.name as name2,
                    LOWER(p1.name) as lower_name
                FROM players p1
                JOIN players p2 ON LOWER(p1.name) = LOWER(p2.name) AND p1.id < p2.id
                WHERE p1.name != p2.name
            ),
            mapped_variations AS (
                SELECT DISTINCT
                    original_player_id,
                    correct_player_id
                FROM sub_match_player_mappings
            )
            SELECT COUNT(*) as remaining
            FROM case_variations cv
            LEFT JOIN mapped_variations mv ON (
                (cv.id1 = mv.original_player_id AND cv.id2 = mv.correct_player_id)
                OR
                (cv.id2 = mv.original_player_id AND cv.id1 = mv.correct_player_id)
            )
            WHERE mv.original_player_id IS NULL
        """)

        remaining = cursor.fetchone()['remaining']
        print(f"Återstående omappade case-variationer: {remaining}")

        # Räkna totala mappningar
        cursor.execute("SELECT COUNT(*) as total FROM sub_match_player_mappings")
        total_mappings = cursor.fetchone()['total']
        print(f"Totala mappningar i systemet: {total_mappings}")

def main():
    print("=== CASE-VARIATION FIXER ===")

    # Fixa alla case-variationer automatiskt
    fix_case_variations()

    # Verifiera resultatet
    verify_case_mappings()

if __name__ == "__main__":
    main()