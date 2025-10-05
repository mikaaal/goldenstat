#!/usr/bin/env python3
"""
Validera mappningar genom att kontrollera att spelarnas matcher stämmer
"""
import sqlite3
import random

def get_recent_mappings(limit=30):
    """Hämta de senaste mappningarna för validering"""
    with sqlite3.connect("goldenstat.db") as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Hämta de senaste mappningarna (från case-variation fix)
        cursor.execute("""
            SELECT
                smpm.sub_match_id,
                smpm.original_player_id,
                smpm.correct_player_id,
                smpm.correct_player_name,
                smpm.mapping_reason,
                smpm.notes
            FROM sub_match_player_mappings smpm
            WHERE smpm.mapping_reason IN (
                'Automatic case variation mapping',
                'Manual case variation mapping - final cleanup'
            )
            ORDER BY RANDOM()
            LIMIT ?
        """, (limit,))

        return cursor.fetchall()

def validate_single_mapping(mapping):
    """Validera en enskild mappning grundligt"""
    with sqlite3.connect("goldenstat.db") as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        sub_match_id = mapping['sub_match_id']
        original_id = mapping['original_player_id']
        correct_id = mapping['correct_player_id']

        print(f"\n=== VALIDERAR MAPPNING ===")
        print(f"Sub-match ID: {sub_match_id}")
        print(f"Original spelare ID: {original_id}")
        print(f"Korrekt spelare ID: {correct_id}")
        print(f"Mappning: {mapping['mapping_reason']}")

        # 1. Kontrollera att original spelare finns och har namn
        cursor.execute("SELECT id, name FROM players WHERE id = ?", (original_id,))
        original_player = cursor.fetchone()

        cursor.execute("SELECT id, name FROM players WHERE id = ?", (correct_id,))
        correct_player = cursor.fetchone()

        if not original_player:
            print(f"PROBLEM: Original spelare ID {original_id} existerar inte!")
            return False

        if not correct_player:
            print(f"PROBLEM: Korrekt spelare ID {correct_id} existerar inte!")
            return False

        print(f"Original: '{original_player['name']}'")
        print(f"Korrekt: '{correct_player['name']}'")
        print(f"Mappad till: '{mapping['correct_player_name']}'")

        # 2. Kontrollera att namnen är case-variationer eller liknande
        if original_player['name'].lower() != correct_player['name'].lower():
            print(f"VARNING: Namnen är inte case-variationer!")
            print(f"   '{original_player['name'].lower()}' vs '{correct_player['name'].lower()}'")

        # 3. Kontrollera att original spelare spelade i denna sub-match
        cursor.execute("""
            SELECT smp.team_number, t.name as team_name, m.season, m.match_date
            FROM sub_match_participants smp
            JOIN sub_matches sm ON smp.sub_match_id = sm.id
            JOIN matches m ON sm.match_id = m.id
            JOIN teams t ON (
                CASE WHEN smp.team_number = 1 THEN m.team1_id ELSE m.team2_id END
            ) = t.id
            WHERE smp.sub_match_id = ? AND smp.player_id = ?
        """, (sub_match_id, original_id))

        original_participation = cursor.fetchone()

        if not original_participation:
            print(f"PROBLEM: Original spelare deltog INTE i sub-match {sub_match_id}!")
            return False

        print(f"Original deltog: Team {original_participation['team_number']}, {original_participation['team_name']}")
        print(f"Säsong: {original_participation['season']}, Datum: {original_participation['match_date']}")

        # 4. Kontrollera att korrekt spelare INTE redan deltog i samma sub-match
        cursor.execute("""
            SELECT COUNT(*) as count
            FROM sub_match_participants smp
            WHERE smp.sub_match_id = ? AND smp.player_id = ?
        """, (sub_match_id, correct_id))

        correct_already_playing = cursor.fetchone()['count']

        if correct_already_playing > 0:
            print(f"PROBLEM: Korrekt spelare spelade redan i samma sub-match!")
            return False

        # 5. Kontrollera statistik för båda spelarna
        cursor.execute("""
            SELECT COUNT(*) as total_matches
            FROM sub_match_participants smp
            WHERE smp.player_id = ?
        """, (original_id,))
        original_matches = cursor.fetchone()['total_matches']

        cursor.execute("""
            SELECT COUNT(*) as total_matches
            FROM sub_match_participants smp
            WHERE smp.player_id = ?
        """, (correct_id,))
        correct_matches = cursor.fetchone()['total_matches']

        cursor.execute("""
            SELECT COUNT(*) as mapped_matches
            FROM sub_match_player_mappings smpm
            WHERE smpm.correct_player_id = ?
        """, (correct_id,))
        mapped_to_correct = cursor.fetchone()['mapped_matches']

        print(f"Matcher - Original: {original_matches}, Korrekt: {correct_matches}")
        print(f"Totala mappningar till korrekt spelare: {mapped_to_correct}")

        # 6. Kontrollera att detta är rimlig mappning (korrekt spelare har fler matcher)
        if original_matches > correct_matches and mapped_to_correct < original_matches:
            print(f"VARNING: Original har fler matcher ({original_matches}) än korrekt ({correct_matches})")

        print(f"OK: Mappning verkar korrekt!")
        return True

def validate_mappings_batch():
    """Validera en batch av mappningar"""
    print("=== MAPPNING VALIDERING ===")

    mappings = get_recent_mappings(30)
    print(f"Hämtade {len(mappings)} mappningar för validering...")

    valid_count = 0
    invalid_count = 0

    for i, mapping in enumerate(mappings, 1):
        print(f"\n--- VALIDERING {i}/30 ---")

        try:
            if validate_single_mapping(mapping):
                valid_count += 1
            else:
                invalid_count += 1

            # Visa progress efter varje 5:e
            if i % 5 == 0:
                print(f"--- Progress: Validerat {i}/30 ---")

        except Exception as e:
            print(f"FEL vid validering: {e}")
            invalid_count += 1

    print(f"\n=== VALIDERING SLUTFORD ===")
    print(f"Korrekta mappningar: {valid_count}")
    print(f"Problematiska mappningar: {invalid_count}")
    print(f"Framgangsgrad: {valid_count/(valid_count+invalid_count)*100:.1f}%")

def check_overall_mapping_health():
    """Kontrollera övergripande hälsa för mappningssystemet"""
    print(f"\n=== SYSTEMHÄLSA KONTROLL ===")

    with sqlite3.connect("goldenstat.db") as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # 1. Kontrollera att alla mappningar pekar på existerande spelare
        cursor.execute("""
            SELECT COUNT(*) as broken_mappings
            FROM sub_match_player_mappings smpm
            LEFT JOIN players p1 ON smpm.original_player_id = p1.id
            LEFT JOIN players p2 ON smpm.correct_player_id = p2.id
            WHERE p1.id IS NULL OR p2.id IS NULL
        """)
        broken_mappings = cursor.fetchone()['broken_mappings']

        # 2. Kontrollera att inga mappningar pekar på sig själva
        cursor.execute("""
            SELECT COUNT(*) as self_mappings
            FROM sub_match_player_mappings smpm
            WHERE smpm.original_player_id = smpm.correct_player_id
        """)
        self_mappings = cursor.fetchone()['self_mappings']

        # 3. Kontrollera dubbletter i mappningar
        cursor.execute("""
            SELECT COUNT(*) as duplicate_mappings
            FROM (
                SELECT sub_match_id, original_player_id, COUNT(*) as count
                FROM sub_match_player_mappings
                GROUP BY sub_match_id, original_player_id
                HAVING COUNT(*) > 1
            )
        """)
        duplicate_mappings = cursor.fetchone()['duplicate_mappings']

        print(f"Brutna mappningar (pekar på obefintliga spelare): {broken_mappings}")
        print(f"Själv-mappningar (spelare mappad till sig själv): {self_mappings}")
        print(f"Duplikat-mappningar (samma sub-match+player mappat flera gånger): {duplicate_mappings}")

        if broken_mappings == 0 and self_mappings == 0 and duplicate_mappings == 0:
            print(f"OK: Mappningssystemet ar friskt!")
        else:
            print(f"VARNING: Mappningssystemet har problem som bor atgardas")

def main():
    print("=== MAPPNING VALIDERING SCRIPT ===")

    # Kontrollera systemhälsa först
    check_overall_mapping_health()

    # Validera 30 mappningar
    validate_mappings_batch()

if __name__ == "__main__":
    main()