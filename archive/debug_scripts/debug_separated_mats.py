#!/usr/bin/env python3
"""
Debug separated_players systemet för Mats
"""
from smart_import_handler import SmartPlayerMatcher

def debug_separated_mats():
    """Debug separated_players för Mats"""
    print("=== DEBUG SEPARATED PLAYERS - MATS ===")

    matcher = SmartPlayerMatcher("goldenstat.db")

    # Kolla om Mats finns i separated_players
    print("Separated players som börjar med 'Mats':")
    for base_name, variants in matcher.separated_players.items():
        if base_name.lower().startswith('mats'):
            print(f"\nBase: {base_name}")
            for variant in variants:
                print(f"  ID {variant['id']}: {variant['full_name']} (club: {variant['club']})")

    # Testa direkt club-specific matching för Mats + Dartanjang
    print(f"\n=== TESTA CLUB-SPECIFIC MATCHING ===")

    # Kolla om "Mats" finns som base name
    if "Mats" in matcher.separated_players:
        print(f"Base 'Mats' finns med {len(matcher.separated_players['Mats'])} varianter:")
        for variant in matcher.separated_players['Mats']:
            print(f"  {variant['full_name']} (club: {variant['club']})")

            # Kolla om Dartanjang matchar
            if variant['club'].lower() == 'dartanjang':
                print(f"    [MATCH] Exact match för Dartanjang!")

            # Kolla standardized matching
            standardized_club = matcher.standardize_club_name(variant['club'])
            dartanjang_standardized = matcher.standardize_club_name('Dartanjang')

            if standardized_club.lower() == dartanjang_standardized.lower():
                print(f"    [STANDARDIZED MATCH] {variant['club']} -> {standardized_club} matches {dartanjang_standardized}")
    else:
        print(f"Base 'Mats' finns INTE i separated_players")

    # Testa även case-insensitive
    for base_name in matcher.separated_players.keys():
        if base_name.lower() == 'mats':
            print(f"Case-insensitive match: '{base_name}' (case mismatch)")

if __name__ == "__main__":
    debug_separated_mats()