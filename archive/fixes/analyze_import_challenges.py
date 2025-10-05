#!/usr/bin/env python3
"""
Analysera utmaningar för framtida import med våra mappningar och separationer
"""
import sqlite3

def analyze_separated_players():
    """Analysera spelare som blivit separerade per klubb"""
    print("=== SEPARERADE SPELARE (MULTICLUB-FIXAR) ===")

    with sqlite3.connect("goldenstat.db") as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Hitta alla spelare med klubb i parenteser
        cursor.execute("""
            SELECT id, name
            FROM players
            WHERE name LIKE '% (%)'
            AND id >= 2314  -- Från våra senaste fixar
            ORDER BY name
        """)

        separated_players = cursor.fetchall()

        print(f"Separerade spelare ({len(separated_players)} st):")

        # Gruppera per basnamn
        base_names = {}
        for player in separated_players:
            # Extrahera basnamn (före parenteser)
            base_name = player['name'].split(' (')[0]

            if base_name not in base_names:
                base_names[base_name] = []
            base_names[base_name].append(player)

        for base_name, variants in base_names.items():
            print(f"\n'{base_name}' har {len(variants)} klubb-varianter:")
            for variant in variants:
                # Räkna matcher
                cursor.execute("""
                    SELECT COUNT(*) as direct_matches
                    FROM sub_match_participants smp
                    WHERE smp.player_id = ?
                """, (variant['id'],))
                direct = cursor.fetchone()['direct_matches']

                cursor.execute("""
                    SELECT COUNT(*) as mapped_matches
                    FROM sub_match_player_mappings smpm
                    WHERE smpm.correct_player_id = ?
                """, (variant['id'],))
                mapped = cursor.fetchone()['mapped_matches']

                print(f"  - {variant['name']}: {direct + mapped} matcher ({direct} direkta + {mapped} mappade)")

        return base_names

def analyze_mapped_players():
    """Analysera alla mappningar vi skapat"""
    print(f"\n=== MAPPNINGAR ANALYS ===")

    with sqlite3.connect("goldenstat.db") as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Räkna mappningar per typ
        cursor.execute("""
            SELECT mapping_reason, COUNT(*) as count
            FROM sub_match_player_mappings
            GROUP BY mapping_reason
            ORDER BY count DESC
        """)

        mapping_types = cursor.fetchall()

        print("Mappningar per typ:")
        for mapping in mapping_types:
            print(f"  {mapping['mapping_reason']}: {mapping['count']} mappningar")

        # Hitta alla "original" spelare som nu är mappade
        cursor.execute("""
            SELECT DISTINCT
                smpm.original_player_id,
                p.name as original_name,
                smpm.correct_player_name
            FROM sub_match_player_mappings smpm
            JOIN players p ON smpm.original_player_id = p.id
            ORDER BY p.name
        """)

        mapped_originals = cursor.fetchall()

        print(f"\nSpelare som nu är mappade till andra ({len(mapped_originals)} st):")
        for i, mapped in enumerate(mapped_originals[:20], 1):  # Visa första 20
            print(f"  {i}. '{mapped['original_name']}' -> '{mapped['correct_player_name']}'")

        if len(mapped_originals) > 20:
            print(f"  ... och {len(mapped_originals) - 20} fler")

def identify_import_challenges(separated_players):
    """Identifiera specifika utmaningar för import"""
    print(f"\n=== IMPORT UTMANINGAR ===")

    challenges = []

    print("1. KLUBB-SEPARERADE SPELARE:")
    print("   Problem: Import kommer med bara 'Mats Andersson', men vi har nu:")
    for base_name, variants in separated_players.items():
        if len(variants) > 1:
            club_names = []
            for variant in variants:
                # Extrahera klubb från parenteser
                club = variant['name'].split(' (')[1].rstrip(')')
                club_names.append(club)
            print(f"     '{base_name}' -> {', '.join(club_names)}")

            challenges.append({
                'type': 'klubb_separation',
                'base_name': base_name,
                'variants': club_names
            })

    print(f"\n2. CASE-VARIATIONER:")
    print("   Problem: Import kan komma med 'mats andersson' men vi förväntar 'Mats Andersson'")

    print(f"\n3. BINDESTRECK/MELLANSLAG:")
    print("   Problem: Import kan komma med 'Lars Erik Renström' men vi förväntar 'Lars-Erik Renström'")

    print(f"\n4. UNICODE-NORMALISERING:")
    print("   Problem: Olika Unicode-representationer av samma klubbnamn")

    return challenges

def suggest_import_strategy(challenges):
    """Föreslå strategi för import"""
    print(f"\n=== FÖRSLAG IMPORT-STRATEGI ===")

    print("STEG 1: PRE-PROCESSING")
    print("  - Normalisera Unicode (NFKC)")
    print("  - Standardisera klubbnamn med samma logik som tidigare")
    print("  - Detektera case-variationer")
    print("  - Detektera bindestreck/mellanslag variationer")

    print(f"\nSTEG 2: SPELARE-MATCHNING")
    print("  För varje inkommande spelare:")
    print("  1. Sök exakt matchning först")
    print("  2. Om inte hittat, sök case-insensitive")
    print("  3. Om multiclub-situation, identifiera korrekt klubb-variant")
    print("  4. Skapa mappning om nödvändigt")

    print(f"\nSTEG 3: KLUB-DISAMBIGUATION")
    print("  För separerade spelare:")
    for challenge in challenges:
        if challenge['type'] == 'klubb_separation':
            print(f"    '{challenge['base_name']}' + lag-info -> rätt variant")

    print(f"\nSTEG 4: FALLBACK-HANTERING")
    print("  - Om osäker, logga för manuell granskning")
    print("  - Använd confidence-scores")
    print("  - Undvik att skapa nya dubletter")

def main():
    print("=== IMPORT UTMANINGS-ANALYS ===")

    # Analysera separerade spelare
    separated = analyze_separated_players()

    # Analysera mappningar
    analyze_mapped_players()

    # Identifiera utmaningar
    challenges = identify_import_challenges(separated)

    # Föreslå strategi
    suggest_import_strategy(challenges)

if __name__ == "__main__":
    main()