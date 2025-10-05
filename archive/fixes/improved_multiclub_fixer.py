#!/usr/bin/env python3
"""
Improved multiclub fixer with better name standardization
"""
import sqlite3
import re
from collections import defaultdict

def standardize_club_name(team_name):
    """Standardize club names to handle variations of the same club"""

    # Remove division info first
    patterns = [
        r'\s*\([^)]*\)$',  # Remove anything in parentheses at end
        r'\s*(SL\d+|DS|\d+[A-Z]+|\d+F[A-Z]+|Superligan)$',  # Remove division codes
    ]

    club = team_name
    for pattern in patterns:
        club = re.sub(pattern, '', club).strip()

    # Remove zero-width spaces and normalize unicode
    import unicodedata
    club = unicodedata.normalize('NFKC', club)
    club = re.sub(r'[\u200b-\u200f\u2060\ufeff]', '', club)  # Remove zero-width spaces

    # Standardize known club variations
    standardizations = {
        # AIK variations
        'AIK': 'AIK Dart',
        'AIK Dart': 'AIK Dart',
        'AIK Dartförening': 'AIK Dart',
        'Solna AIK': 'AIK Dart',

        # HMT variations
        'HMT Dart': 'HMT Dart',
        'Engelen': 'HMT Dart',  # Engelen seems to be HMT Dart

        # TYO variations (after Unicode normalization, these should be the same)
        'TYO DC': 'TYO DC',

        # DK variations (after Unicode normalization, these should be the same)
        'DK Pilo': 'DK Pilo',

        # Mitt i DC variations (after Unicode normalization, these should be the same)
        'Mitt i DC': 'Mitt i DC',

        # AC DC variations (after Unicode normalization, these should be the same)
        'AC DC': 'AC DC',

        # East Enders variations
        'East Enders': 'East Enders',

        # Järfälla variations (probable typo)
        'Järfälla': 'Järfälla',
        'Järfalla': 'Järfälla',  # Typo fix

        # Spikkastarna variations
        'SpikKastarna': 'SpikKastarna',
        'Spikkastarna B': 'SpikKastarna',  # B-lag är samma klubb
    }

    return standardizations.get(club, club)

def verify_existing_fixes():
    """Verify that existing fixes are correct"""
    print("=== VERIFIERAR BEFINTLIGA FIXAR ===")

    with sqlite3.connect("goldenstat.db") as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Hitta alla spelare som verkar vara fixade (har klubbnamn i parenteser)
        cursor.execute("""
            SELECT id, name FROM players
            WHERE name LIKE '% (%'
            AND id >= 2320  -- Nya spelare från senaste fix
            ORDER BY id
        """)

        fixed_players = cursor.fetchall()

        print(f"Hittade {len(fixed_players)} nyligen fixade spelare:")

        for player in fixed_players:
            # Räkna totala matcher för denna spelare
            cursor.execute("""
                SELECT COUNT(*) as direct_matches
                FROM sub_match_participants smp
                WHERE smp.player_id = ?
            """, (player['id'],))

            direct = cursor.fetchone()['direct_matches']

            cursor.execute("""
                SELECT COUNT(*) as mapped_matches
                FROM sub_match_player_mappings smpm
                WHERE smpm.correct_player_id = ?
            """, (player['id'],))

            mapped = cursor.fetchone()['mapped_matches']

            total = direct + mapped

            # Kontrollera klubbtillhörighet
            cursor.execute("""
                SELECT DISTINCT t.name as team_name, m.season
                FROM sub_match_player_mappings smpm
                JOIN sub_matches sm ON smpm.sub_match_id = sm.id
                JOIN matches m ON sm.match_id = m.id
                JOIN teams t ON (
                    SELECT CASE WHEN smp2.team_number = 1 THEN m.team1_id ELSE m.team2_id END
                    FROM sub_match_participants smp2
                    WHERE smp2.sub_match_id = sm.id AND smp2.player_id = smpm.original_player_id
                ) = t.id
                WHERE smpm.correct_player_id = ?
                ORDER BY m.season, t.name
            """, (player['id'],))

            teams = cursor.fetchall()

            print(f"\n  ID {player['id']}: {player['name']} - {total} matcher")

            if teams:
                clubs = set(standardize_club_name(team['team_name']) for team in teams)
                if len(clubs) > 1:
                    print(f"    PROBLEM: Fortfarande flera klubbar: {', '.join(clubs)}")
                else:
                    print(f"    OK: En klubb ({list(clubs)[0]})")
            else:
                print(f"    Inga mappade matcher")

def find_improved_multiclub_problems():
    """Find multiclub problems with improved standardization"""
    print("\n=== HITTA MULTICLUB-PROBLEM (FÖRBÄTTRAD) ===")

    with sqlite3.connect("goldenstat.db") as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Hitta spelare med fullständiga namn som har multiclub-problem
        cursor.execute("""
            SELECT
                p.id,
                p.name,
                m.season,
                t.name as team_name,
                COUNT(*) as matches
            FROM sub_match_participants smp
            JOIN sub_matches sm ON smp.sub_match_id = sm.id
            JOIN matches m ON sm.match_id = m.id
            JOIN players p ON smp.player_id = p.id
            JOIN teams t ON (
                CASE WHEN smp.team_number = 1 THEN m.team1_id ELSE m.team2_id END
            ) = t.id
            WHERE p.name LIKE '% %'  -- Har mellanslag (fullständigt namn)
            AND p.name NOT LIKE '% (%'  -- Inte redan klubb-specificerade
            GROUP BY p.id, p.name, m.season, t.name
            ORDER BY p.id, m.season
        """)

        all_data = cursor.fetchall()

        # Gruppera per spelare och säsong
        player_seasons = {}
        for row in all_data:
            key = (row['id'], row['name'], row['season'])
            if key not in player_seasons:
                player_seasons[key] = []

            standardized_club = standardize_club_name(row['team_name'])
            player_seasons[key].append({
                'team_name': row['team_name'],
                'club_name': standardized_club,
                'matches': row['matches']
            })

        # Hitta verkliga multiclub-problem
        real_problems = []
        for (player_id, player_name, season), teams in player_seasons.items():
            clubs = set(team['club_name'] for team in teams)

            if len(clubs) > 1:  # Flera klubbar efter standardisering
                total_matches = sum(team['matches'] for team in teams)
                real_problems.append({
                    'id': player_id,
                    'name': player_name,
                    'season': season,
                    'clubs': list(clubs),
                    'teams': teams,
                    'club_count': len(clubs),
                    'total_matches': total_matches
                })

        # Sortera efter antal klubbar och matcher
        real_problems.sort(key=lambda x: (x['club_count'], x['total_matches']), reverse=True)

        print(f"Hittade {len(real_problems)} verkliga multiclub-problem (efter förbättrad standardisering):")

        for i, problem in enumerate(real_problems[:10], 1):
            print(f"\n{i}. ID {problem['id']}: {problem['name']} ({problem['season']})")
            print(f"   {problem['club_count']} klubbar, {problem['total_matches']} matcher")

            for club in problem['clubs']:
                club_teams = [t for t in problem['teams'] if t['club_name'] == club]
                club_matches = sum(t['matches'] for t in club_teams)
                original_names = [t['team_name'] for t in club_teams]
                print(f"   -> {club}: {club_matches} matcher")
                print(f"      Original: {', '.join(original_names)}")

        if len(real_problems) > 10:
            print(f"\n... och {len(real_problems) - 10} fler")

        return real_problems

def fix_batch_of_problems(problems, batch_size=5):
    """Fix a batch of multiclub problems"""
    print(f"\n=== FIXAR BATCH AV {batch_size} PROBLEM ===")

    # Gruppera problem per spelare
    player_problems = defaultdict(list)
    for problem in problems:
        player_problems[(problem['id'], problem['name'])].append(problem)

    fixed_count = 0
    for (player_id, player_name), season_problems in list(player_problems.items())[:batch_size]:
        try:
            print(f"\n--- Fixar {player_name} (ID {player_id}) ---")
            fix_specific_player_improved(player_id, player_name, season_problems)
            fixed_count += 1
        except Exception as e:
            print(f"FEL vid fix av {player_name}: {e}")

    return fixed_count

def fix_specific_player_improved(player_id, player_name, season_problems):
    """Fix a specific player with improved logic"""

    with sqlite3.connect("goldenstat.db") as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Samla alla unika klubbar från alla säsonger
        all_clubs = set()
        for season_data in season_problems:
            all_clubs.update(season_data['clubs'])

        all_clubs = list(all_clubs)

        # Skapa separata spelare för varje klubb
        club_player_mapping = {}

        print(f"Skapar spelare för klubbar: {', '.join(all_clubs)}")

        for i, club in enumerate(all_clubs):
            if i == 0:
                # Första klubben behåller original player_id
                club_player_mapping[club] = player_id
                cursor.execute("UPDATE players SET name = ? WHERE id = ?",
                             (f"{player_name} ({club})", player_id))
                print(f"  Uppdaterade original: ID {player_id} -> '{player_name} ({club})'")
            else:
                # Skapa ny spelare för andra klubbar
                cursor.execute("INSERT INTO players (name) VALUES (?)",
                             (f"{player_name} ({club})",))
                new_player_id = cursor.lastrowid
                club_player_mapping[club] = new_player_id
                print(f"  Skapade ny spelare: ID {new_player_id} -> '{player_name} ({club})'")

        # Skapa mappningar
        cursor.execute("""
            SELECT DISTINCT
                smp.sub_match_id,
                t.name as team_name,
                m.season
            FROM sub_match_participants smp
            JOIN sub_matches sm ON smp.sub_match_id = sm.id
            JOIN matches m ON sm.match_id = m.id
            JOIN teams t ON (
                CASE WHEN smp.team_number = 1 THEN m.team1_id ELSE m.team2_id END
            ) = t.id
            WHERE smp.player_id = ?
        """, (player_id,))

        matches = cursor.fetchall()

        mappings_created = 0
        for match in matches:
            standardized_club = standardize_club_name(match['team_name'])
            target_player_id = club_player_mapping.get(standardized_club)

            if target_player_id and target_player_id != player_id:
                # Skapa mapping
                cursor.execute("""
                    INSERT OR REPLACE INTO sub_match_player_mappings (
                        sub_match_id,
                        original_player_id,
                        correct_player_id,
                        correct_player_name,
                        match_context,
                        confidence,
                        mapping_reason,
                        notes
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    match['sub_match_id'],
                    player_id,
                    target_player_id,
                    f"{player_name} ({standardized_club})",
                    f"Multiclub fix for {match['season']}",
                    95,
                    "Multiclub separation with improved standardization",
                    f"Split {player_name}, standardized club: {standardized_club}"
                ))
                mappings_created += 1

        conn.commit()
        print(f"  Skapade {mappings_created} mappningar")

def main():
    print("=== FÖRBÄTTRAD MULTICLUB FIXER ===")

    # Steg 1: Verifiera befintliga fixar
    verify_existing_fixes()

    # Steg 2: Hitta återstående problem med förbättrad logik
    problems = find_improved_multiclub_problems()

    if not problems:
        print("\nInga återstående multiclub-problem!")
        return

    # Steg 3: Fixa nästa batch automatiskt
    print(f"\nTotalt {len(problems)} problem kvar att fixa")

    if problems:
        fixed_count = fix_batch_of_problems(problems, 5)
        print(f"\n=== SLUTFÖRD BATCH ===")
        print(f"Fixade {fixed_count} spelare")
        print(f"Återstående problem: {len(problems) - fixed_count}")
    else:
        print("Inga problem att fixa!")

if __name__ == "__main__":
    main()