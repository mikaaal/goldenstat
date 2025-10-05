#!/usr/bin/env python3
"""
Debug specifikt Mats från Dartanjang
"""
from smart_import_handler import SmartPlayerMatcher

def debug_mats_dartanjang():
    """Debug vad som händer med Mats från Dartanjang"""
    print("=== DEBUG MATS FRÅN DARTANJANG ===")

    matcher = SmartPlayerMatcher("goldenstat.db")

    # Testa specifikt fall
    result = matcher.find_player_match("Mats", "Dartanjang")

    print(f"Resultat för 'Mats' från 'Dartanjang':")
    print(f"  Action: {result['action']}")
    print(f"  Target: {result['player_name']}")
    print(f"  Player ID: {result.get('player_id', 'None')}")
    print(f"  Confidence: {result['confidence']}%")
    print(f"  Notes: {result['notes']}")

    if result['action'] == 'first_name_mapping_found':
        print(f"  Original name: {result.get('original_name', 'N/A')}")
        print(f"  Mapping type: {result.get('mapping_type', 'N/A')}")

        # Detta borde INTE hända enligt vår nya logik!
        print("\n[ERROR] Detta är fel - vi borde inte hitta en team-context match!")

    # Låt mig också kontrollera extract_club_name
    club_name = matcher.extract_club_name("Dartanjang")
    print(f"\nExtracted club name: '{club_name}'")

    # Kolla också vad som händer med team-kontroll
    import sqlite3
    with sqlite3.connect("goldenstat.db") as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("""
            SELECT DISTINCT smpm.correct_player_name,
                   COUNT(*) as mapping_count,
                   GROUP_CONCAT(DISTINCT
                       CASE WHEN smp.team_number = 1 THEN t1.name ELSE t2.name END
                   ) as mapped_teams
            FROM sub_match_player_mappings smpm
            JOIN players p ON smpm.original_player_id = p.id
            JOIN sub_matches sm ON smpm.sub_match_id = sm.id
            JOIN matches m ON sm.match_id = m.id
            JOIN teams t1 ON m.team1_id = t1.id
            JOIN teams t2 ON m.team2_id = t2.id
            JOIN sub_match_participants smp ON sm.id = smp.sub_match_id
            WHERE p.name = 'Mats' AND smp.player_id = p.id
            GROUP BY smpm.correct_player_name
            ORDER BY mapping_count DESC
        """)

        mappings = cursor.fetchall()
        print(f"\nAlla 'Mats' mappningar i detalj:")

        for mapping in mappings:
            mapped_teams = mapping['mapped_teams'] or ''
            print(f"  -> {mapping['correct_player_name']} ({mapping['mapping_count']}x)")
            print(f"     Teams: {mapped_teams}")

            # Kolla exakt vad matcher
            if "dartanjang" in mapped_teams.lower():
                print(f"     [MATCH] 'dartanjang' finns i mapped_teams (lowercase)")
            elif "Dartanjang" in mapped_teams:
                print(f"     [MATCH] 'Dartanjang' finns i mapped_teams (case sensitive)")
            else:
                print(f"     [NO MATCH] 'Dartanjang' finns INTE i mapped_teams")

if __name__ == "__main__":
    debug_mats_dartanjang()