#!/usr/bin/env python3
"""
Debug team context error - varför mappas spelare till fel lag?
"""
import sqlite3

def debug_team_context_error():
    """Analysera varför Anders från Dartanjang mappas till VH Sportbar"""
    print("=== DEBUG TEAM CONTEXT ERROR ===")

    test_cases = [
        ("Anders", "Dartanjang"),
        ("Mats", "SpikKastarna"),
        ("Mikael", "AIK Dart"),
    ]

    with sqlite3.connect("goldenstat.db") as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        for first_name, team_name in test_cases:
            print(f"\n=== {first_name} från {team_name} ===")

            # Visa alla mappningar för detta förnamn
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
                WHERE p.name = ? AND smp.player_id = p.id
                GROUP BY smpm.correct_player_name
                ORDER BY mapping_count DESC
            """, (first_name,))

            mappings = cursor.fetchall()
            print(f"Alla mappningar för '{first_name}':")

            for mapping in mappings:
                mapped_teams = mapping['mapped_teams'] or ''
                print(f"  -> {mapping['correct_player_name']} ({mapping['mapping_count']}x)")
                print(f"    Lag: {mapped_teams}")

                # Kolla om vårt sök-lag finns i mapped_teams
                if team_name.lower() in mapped_teams.lower():
                    print(f"    [MATCH] {team_name} finns i mapped_teams!")
                else:
                    print(f"    [NO MATCH] {team_name} finns INTE i mapped_teams")

                # Extrahera klubb från team_name och kolla det också
                club_name = team_name.split('(')[0].strip() if '(' in team_name else team_name
                if club_name.lower() in mapped_teams.lower():
                    print(f"    [CLUB MATCH] Club '{club_name}' finns i mapped_teams!")

            # Visa vilken som skulle väljas med nuvarande logik
            if mappings:
                # Hitta den bästa mappningen baserat på klubb-kontext
                best_mapping = None
                club_name = team_name.split('(')[0].strip() if '(' in team_name else team_name

                for mapping in mappings:
                    mapped_teams = mapping['mapped_teams'] or ''
                    if club_name in mapped_teams:
                        best_mapping = mapping
                        break

                # Om ingen klubb-matchning, ta den med flest mappningar
                if not best_mapping:
                    best_mapping = mappings[0]

                print(f"\nNuvarande logik väljer: {best_mapping['correct_player_name']}")
                print(f"Anledning: {'Team context match' if club_name in (best_mapping['mapped_teams'] or '') else 'Most frequent mapping (no team match)'}")

if __name__ == "__main__":
    debug_team_context_error()