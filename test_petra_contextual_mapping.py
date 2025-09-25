#!/usr/bin/env python3
"""
Testa att Petra från Sweden Capital skulle få korrekt kontextuell mappning
"""
from smart_season_importer import SmartSeasonImporter

def test_petra_contextual_mapping():
    """Testa Petra kontextuell mappning"""
    print("=== TEST PETRA KONTEXTUELL MAPPNING ===")

    importer = SmartSeasonImporter("goldenstat.db")

    # Simulera Petra från Sweden Capital
    test_cases = [
        ("Petra", "Sweden Capital (2FB)"),
        ("Petra", "Sweden Capital"),
        ("Magnus", "Old Bowler (2FB)"),
        ("Anna", "Cobra DC (2FB)"),
    ]

    for player_name, team_name in test_cases:
        print(f"\nTest: '{player_name}' från '{team_name}'")

        # Första testa SmartPlayerMatcher direkt
        result = importer.matcher.find_player_match(player_name, team_name)
        print(f"  SmartPlayerMatcher result:")
        print(f"    Action: {result['action']}")
        print(f"    Target: {result['player_name']}")
        print(f"    Confidence: {result['confidence']}%")

        # Sedan testa vad get_smart_player_id skulle göra
        mock_sub_match_id = 999999

        try:
            # Vi kan inte köra detta på riktigt utan att förstöra data, så bara simulera logiken
            if result['confidence'] < 90 and ' ' not in player_name and len(player_name) >= 3:
                club_name = importer.extract_club_name(team_name)
                contextual_name = f"{player_name} ({club_name})"

                print(f"  get_smart_player_id skulle skapa:")
                print(f"    Kontextuell mappning: {player_name} -> {contextual_name}")
                print(f"    Club: {club_name}")
                print(f"    Action: AUTO_CREATE_CONTEXTUAL_MAPPING")
            else:
                print(f"  get_smart_player_id skulle använda befintlig logik")
        except Exception as e:
            print(f"  Simulering fel: {e}")

    # Kolla också vad som finns för Petra redan
    print(f"\n=== BEFINTLIGA PETRA-SPELARE ===")
    import sqlite3
    with sqlite3.connect("goldenstat.db") as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("SELECT id, name FROM players WHERE name LIKE 'Petra%' ORDER BY name")
        petra_players = cursor.fetchall()

        for player in petra_players:
            # Kolla om denna spelare skulle vara en target för kontextuell mappning
            if '(' in player['name']:
                club_part = player['name'].split('(')[1].rstrip(')')
                print(f"  ID {player['id']}: {player['name']} -> club: '{club_part}'")
            else:
                print(f"  ID {player['id']}: {player['name']} (generisk)")

if __name__ == "__main__":
    test_petra_contextual_mapping()