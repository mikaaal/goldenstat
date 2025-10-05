#!/usr/bin/env python3
"""
Find players with multi-team issues that don't have mappings yet
"""
import sqlite3

def find_unmapped_multiteam_problems():
    """Find players with multi-team issues who don't have mappings"""
    print("=== SPELARE MED MULTI-TEAM PROBLEM SOM SAKNAR MAPPNINGAR ===")

    with sqlite3.connect("goldenstat.db") as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Hitta spelare som spelar för flera lag men INTE har mappningar
        cursor.execute("""
            WITH multiteam_players AS (
                SELECT
                    p.id,
                    p.name,
                    m.season,
                    COUNT(DISTINCT t.id) as team_count,
                    COUNT(*) as total_matches,
                    GROUP_CONCAT(DISTINCT t.name) as teams
                FROM sub_match_participants smp
                JOIN sub_matches sm ON smp.sub_match_id = sm.id
                JOIN matches m ON sm.match_id = m.id
                JOIN players p ON smp.player_id = p.id
                JOIN teams t ON (
                    CASE WHEN smp.team_number = 1 THEN m.team1_id ELSE m.team2_id END
                ) = t.id
                GROUP BY p.id, p.name, m.season
                HAVING COUNT(DISTINCT t.id) > 1
            ),
            mapped_players AS (
                SELECT DISTINCT original_player_id
                FROM sub_match_player_mappings
            )
            SELECT
                mp.*,
                CASE WHEN map.original_player_id IS NULL THEN 'Ej mappad' ELSE 'Mappad' END as mapping_status
            FROM multiteam_players mp
            LEFT JOIN mapped_players map ON mp.id = map.original_player_id
            WHERE map.original_player_id IS NULL  -- Bara omappade
            ORDER BY mp.team_count DESC, mp.total_matches DESC
        """)

        unmapped = cursor.fetchall()

        print(f"Hittade {len(unmapped)} spelare/säsong kombinationer som INTE har mappningar:")

        for i, player in enumerate(unmapped[:20]):  # Visa första 20
            print(f"\n{i+1}. ID {player['id']}: {player['name']} ({player['season']})")
            print(f"   {player['team_count']} lag, {player['total_matches']} matcher")
            print(f"   Lag: {player['teams'][:80]}...")

        if len(unmapped) > 20:
            print(f"\n... och {len(unmapped) - 20} fler")

        return unmapped

def find_unmapped_case_variations():
    """Find case variations that don't have mappings"""
    print("\n=== CASE-VARIATIONER SOM SAKNAR MAPPNINGAR ===")

    with sqlite3.connect("goldenstat.db") as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Hitta case-variationer som inte har mappningar
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
                WHERE p1.name != p2.name  -- Olika case
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
            WHERE mv.original_player_id IS NULL  -- Inte mappade
            ORDER BY cv.lower_name
        """)

        unmapped_cases = cursor.fetchall()

        print(f"Hittade {len(unmapped_cases)} case-variationer som INTE har mappningar:")

        for i, case in enumerate(unmapped_cases[:15]):  # Visa första 15
            print(f"\n{i+1}. '{case['lower_name']}':")
            print(f"   ID {case['id1']}: '{case['name1']}'")
            print(f"   ID {case['id2']}: '{case['name2']}'")

        if len(unmapped_cases) > 15:
            print(f"\n... och {len(unmapped_cases) - 15} fler")

        return unmapped_cases

def analyze_mapping_coverage():
    """Analyze how much of the problems are already covered by mappings"""
    print("\n=== MAPPNINGSTÄCKNING ANALYS ===")

    with sqlite3.connect("goldenstat.db") as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Räkna totalt antal spelare med multi-team problem
        cursor.execute("""
            SELECT COUNT(DISTINCT p.id) as total_multiteam_players
            FROM sub_match_participants smp
            JOIN sub_matches sm ON smp.sub_match_id = sm.id
            JOIN matches m ON sm.match_id = m.id
            JOIN players p ON smp.player_id = p.id
            JOIN teams t ON (
                CASE WHEN smp.team_number = 1 THEN m.team1_id ELSE m.team2_id END
            ) = t.id
            GROUP BY p.id, m.season
            HAVING COUNT(DISTINCT t.id) > 1
        """)

        total_multiteam = cursor.fetchone()['total_multiteam_players']

        # Räkna hur många som har mappningar
        cursor.execute("""
            SELECT COUNT(DISTINCT original_player_id) as mapped_players
            FROM sub_match_player_mappings
        """)

        mapped_players = cursor.fetchone()['mapped_players']

        # Räkna case-variationer
        cursor.execute("""
            SELECT COUNT(*) as total_case_variations
            FROM (
                SELECT LOWER(name) as lower_name
                FROM players
                GROUP BY LOWER(name)
                HAVING COUNT(*) > 1
            )
        """)

        case_variations = cursor.fetchone()['total_case_variations']

        print(f"Multi-team spelare totalt: {total_multiteam}")
        print(f"Spelare med mappningar: {mapped_players}")
        print(f"Täckning: {mapped_players/total_multiteam*100:.1f}%")
        print(f"Case-variationer totalt: {case_variations}")

def suggest_next_actions(unmapped_multiteam, unmapped_cases):
    """Suggest prioritized actions"""
    print("\n=== FÖRESLAGNA NÄSTA STEG ===")

    print("1. HÖGSTA PRIORITET - Multi-team spelare utan mappningar:")
    if unmapped_multiteam:
        worst_cases = sorted(unmapped_multiteam, key=lambda x: x['team_count'], reverse=True)[:5]
        for case in worst_cases:
            print(f"   - {case['name']} (ID {case['id']}): {case['team_count']} lag")

    print("\n2. MEDIUM PRIORITET - Case-variationer:")
    print(f"   - {len(unmapped_cases)} case-variationer kan mappas automatiskt")

    print("\n3. LÅG PRIORITET - Manuell granskning:")
    print("   - Kontrollera om automatiska mappningar är korrekta")

def main():
    print("=== OMAPPADE PROBLEM DETEKTOR ===")

    # Hitta omappade problem
    unmapped_multiteam = find_unmapped_multiteam_problems()
    unmapped_cases = find_unmapped_case_variations()

    # Analysera täckning
    analyze_mapping_coverage()

    # Föreslå åtgärder
    suggest_next_actions(unmapped_multiteam, unmapped_cases)

if __name__ == "__main__":
    main()