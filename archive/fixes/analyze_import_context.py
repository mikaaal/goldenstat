#!/usr/bin/env python3
"""
Analysera vilken kontext som finns tillgänglig under import
"""
from smart_season_importer import SmartSeasonImporter

def analyze_import_context():
    """Analysera vad som är tillgängligt under import för klubb-kontext"""
    print("=== ANALYS AV IMPORT-KONTEXT ===")

    importer = SmartSeasonImporter("goldenstat.db")

    # Simulera en import-situation
    print("Under import har vi tillgång till:")
    print("1. raw_player_name: 'Mats'")
    print("2. team_name: 'Dartanjang (2FB)' eller 'Dartanjang'")
    print("3. sub_match_id: specifikt sub-match ID")
    print("4. SmartPlayerMatcher med alla etablerade mappningar och separerade spelare")

    # Testa extract_club_name
    test_teams = [
        "Dartanjang (2FB)",
        "Dartanjang",
        "Rockhangers (SL1)",
        "AIK Dart",
        "SpikKastarna"
    ]

    print(f"\nExtract club name test:")
    for team in test_teams:
        club = importer.matcher.extract_club_name(team)
        print(f"  '{team}' -> '{club}'")

    # Kolla tillgängliga separerade spelare
    print(f"\nTillgängliga separerade 'Mats' relaterade spelare:")
    for base_name, variants in importer.matcher.separated_players.items():
        if 'mats' in base_name.lower():
            print(f"  Base: {base_name}")
            for variant in variants:
                print(f"    {variant['full_name']} (club: {variant['club']})")

    # Testa vår nuvarande logik
    print(f"\n=== TESTA NUVARANDE LOGIK ===")

    test_cases = [
        ("Mats", "Dartanjang (2FB)"),
        ("Mats", "Dartanjang"),
        ("Johan", "Rockhangers (SL1)"),
        ("Anders", "VH Sportbar"),
        ("Mikael", "Väsby")
    ]

    for player_name, team_name in test_cases:
        print(f"\nTest: '{player_name}' från '{team_name}'")
        result = importer.matcher.find_player_match(player_name, team_name)
        print(f"  Action: {result['action']}")
        print(f"  Target: {result['player_name']}")
        print(f"  Confidence: {result['confidence']}%")

        # Är detta tillräckligt för automatisk import?
        if result['confidence'] >= 90:
            print(f"  [AUTO] Kan importeras automatiskt")
        elif result['confidence'] >= 75:
            print(f"  [REVIEW] Behöver granskning")
        else:
            print(f"  [MANUAL] Kräver manuell hantering")

if __name__ == "__main__":
    analyze_import_context()