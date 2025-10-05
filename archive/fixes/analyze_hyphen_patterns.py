#!/usr/bin/env python3
"""
Analysera bindestreck vs mellanslag mönster i spelarnamn
"""
import sqlite3
import re

def find_hyphen_space_variations():
    """Hitta spelare som kan vara samma person med bindestreck vs mellanslag"""
    print("=== BINDESTRECK VS MELLANSLAG ANALYS ===")

    with sqlite3.connect("goldenstat.db") as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Hämta alla spelare med bindestreck
        cursor.execute("""
            SELECT id, name
            FROM players
            WHERE name LIKE '%-%'
            ORDER BY name
        """)

        hyphenated_players = cursor.fetchall()
        print(f"Spelare med bindestreck: {len(hyphenated_players)}")

        # Hitta potentiella matchningar
        potential_matches = []

        for hyphen_player in hyphenated_players:
            hyphen_name = hyphen_player['name']

            # Skapa version utan bindestreck (ersätt - med mellanslag)
            space_version = hyphen_name.replace('-', ' ')

            # Sök efter exakt matchning eller case-variation
            cursor.execute("""
                SELECT id, name
                FROM players
                WHERE LOWER(name) = LOWER(?)
                AND id != ?
            """, (space_version, hyphen_player['id']))

            matches = cursor.fetchall()

            if matches:
                for match in matches:
                    # Kontrollera att det verkligen är bindestreck/mellanslag skillnad
                    if hyphen_name.replace('-', ' ').lower() == match['name'].lower():
                        potential_matches.append({
                            'hyphen_id': hyphen_player['id'],
                            'hyphen_name': hyphen_name,
                            'space_id': match['id'],
                            'space_name': match['name']
                        })

        print(f"Potentiella bindestreck/mellanslag variationer: {len(potential_matches)}")

        # Visa alla hittade matchningar
        for i, match in enumerate(potential_matches, 1):
            print(f"\n{i}. Bindestreck vs Mellanslag:")
            print(f"   ID {match['hyphen_id']}: \"{match['hyphen_name']}\"")
            print(f"   ID {match['space_id']}: \"{match['space_name']}\"")

            # Kontrollera matcher för varje
            cursor.execute("SELECT COUNT(*) as count FROM sub_match_participants WHERE player_id = ?",
                         (match['hyphen_id'],))
            hyphen_matches = cursor.fetchone()['count']

            cursor.execute("SELECT COUNT(*) as count FROM sub_match_participants WHERE player_id = ?",
                         (match['space_id'],))
            space_matches = cursor.fetchone()['count']

            print(f"   Matcher: {hyphen_matches} vs {space_matches}")

            # Kontrollera om redan mappade
            cursor.execute("""
                SELECT COUNT(*) as count
                FROM sub_match_player_mappings
                WHERE (original_player_id = ? AND correct_player_id = ?)
                OR (original_player_id = ? AND correct_player_id = ?)
            """, (match['hyphen_id'], match['space_id'], match['space_id'], match['hyphen_id']))

            existing_mappings = cursor.fetchone()['count']
            if existing_mappings > 0:
                print(f"   Status: Redan mappad ({existing_mappings} mappningar)")
            else:
                print(f"   Status: INTE mappad")

        return potential_matches

def find_common_hyphen_patterns():
    """Analysera vanliga bindestreck mönster"""
    print(f"\n=== VANLIGA BINDESTRECK MÖNSTER ===")

    with sqlite3.connect("goldenstat.db") as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Hitta alla unika bindestreck mönster
        cursor.execute("""
            SELECT name
            FROM players
            WHERE name LIKE '%-%'
            ORDER BY name
        """)

        hyphenated = cursor.fetchall()

        # Analysera mönster
        patterns = {}

        for player in hyphenated:
            name = player['name']

            # Extrahera mönster (antal ord före och efter bindestreck)
            parts = name.split('-')
            if len(parts) == 2:
                first_words = len(parts[0].strip().split())
                second_words = len(parts[1].strip().split())
                pattern = f"{first_words}-{second_words}"

                if pattern not in patterns:
                    patterns[pattern] = []
                patterns[pattern].append(name)

        print("Bindestreck mönster (ord före-ord efter):")
        for pattern, names in sorted(patterns.items()):
            print(f"\n{pattern} mönster ({len(names)} spelare):")
            for name in names[:5]:  # Visa första 5
                print(f"  - {name}")
            if len(names) > 5:
                print(f"  ... och {len(names) - 5} fler")

def analyze_specific_cases():
    """Analysera specifika intressanta fall"""
    print(f"\n=== SPECIFIKA FALL ANALYS ===")

    with sqlite3.connect("goldenstat.db") as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Sök efter "Lars-Erik" eller liknande
        test_cases = [
            "Lars-Erik%",
            "Per-Erik%",
            "Jan-Erik%",
            "Karl-Erik%",
            "Lars-Ola%",
            "Jan-Ola%"
        ]

        print("Sökning efter vanliga svenska sammansatta förnamn:")

        for pattern in test_cases:
            cursor.execute("""
                SELECT id, name
                FROM players
                WHERE name LIKE ?
                ORDER BY name
            """, (pattern,))

            matches = cursor.fetchall()
            if matches:
                print(f"\n{pattern[:-1]} mönster ({len(matches)} träffar):")
                for match in matches:
                    # Kontrollera matcher
                    cursor.execute("SELECT COUNT(*) as count FROM sub_match_participants WHERE player_id = ?",
                                 (match['id'],))
                    match_count = cursor.fetchone()['count']
                    print(f"  ID {match['id']}: {match['name']} ({match_count} matcher)")

def main():
    print("=== BINDESTRECK/MELLANSLAG MÖNSTER ANALYS ===")

    # Hitta bindestreck vs mellanslag variationer
    matches = find_hyphen_space_variations()

    # Analysera vanliga mönster
    find_common_hyphen_patterns()

    # Specifika fall
    analyze_specific_cases()

    print(f"\n=== SAMMANFATTNING ===")
    print(f"Totalt {len(matches)} potentiella bindestreck/mellanslag variationer hittade")

    unmapped = [m for m in matches if True]  # Alla för nu
    print(f"Dessa behöver undersökas för eventuell mappning")

if __name__ == "__main__":
    main()