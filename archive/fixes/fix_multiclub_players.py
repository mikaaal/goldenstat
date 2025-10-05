#!/usr/bin/env python3
"""
Fix players who play for multiple clubs simultaneously by splitting them into separate players
"""
import sqlite3
import re
from collections import defaultdict

def extract_club_name(team_name):
    """Extract club name from team name (remove division info)"""
    patterns = [
        r'\s*\([^)]*\)$',  # Remove anything in parentheses at end
        r'\s*(SL\d+|DS|\d+[A-Z]+|\d+F[A-Z]+|Superligan)$',  # Remove division codes
    ]

    club = team_name
    for pattern in patterns:
        club = re.sub(pattern, '', club).strip()

    return club

def find_real_multiclub_problems():
    """Find players with genuine multi-club problems (excluding naming variations)"""
    print("=== HITTA VERKLIGA MULTICLUB-PROBLEM ===")

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

            club_name = extract_club_name(row['team_name'])
            player_seasons[key].append({
                'team_name': row['team_name'],
                'club_name': club_name,
                'matches': row['matches']
            })

        # Hitta verkliga multiclub-problem (filtrera bort namnvariationer)
        real_problems = []
        naming_variations = {
            # Kända namnvariationer som är samma klubb
            frozenset(['AIK', 'AIK Dart', 'AIK Dartförening']): 'AIK Dart',
            frozenset(['HMT Dart', 'HMT​Dart', 'Engelen']): 'HMT Dart',
            frozenset(['Sweden Capital']): 'Sweden Capital',
        }

        for (player_id, player_name, season), teams in player_seasons.items():
            clubs = set(team['club_name'] for team in teams)

            if len(clubs) <= 1:
                continue  # Bara en klubb

            # Kolla om detta är namnvariationer
            is_naming_variation = False
            for variation_set, canonical_name in naming_variations.items():
                if clubs.issubset(variation_set):
                    is_naming_variation = True
                    break

            if not is_naming_variation and len(clubs) > 1:
                # Verkligt multiclub-problem
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

        print(f"Hittade {len(real_problems)} verkliga multiclub-problem:")

        for i, problem in enumerate(real_problems[:10], 1):
            print(f"\n{i}. ID {problem['id']}: {problem['name']} ({problem['season']})")
            print(f"   {problem['club_count']} klubbar, {problem['total_matches']} matcher")

            for club in problem['clubs']:
                club_teams = [t for t in problem['teams'] if t['club_name'] == club]
                club_matches = sum(t['matches'] for t in club_teams)
                team_names = [t['team_name'] for t in club_teams]
                print(f"   -> {club}: {club_matches} matcher ({', '.join(team_names)})")

        if len(real_problems) > 10:
            print(f"\n... och {len(real_problems) - 10} fler")

        return real_problems

def fix_specific_player(player_id, player_name, season_problems):
    """Fix a specific player's multiclub problems"""
    print(f"\n=== FIXAR {player_name} (ID {player_id}) ===")

    with sqlite3.connect("goldenstat.db") as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Skapa separata spelare för varje klubb
        club_player_mapping = {}

        for season_data in season_problems:
            season = season_data['season']
            clubs = season_data['clubs']

            print(f"\nSäsong {season}:")

            for i, club in enumerate(clubs):
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

        # Skapa mappningar för att dirigera matcher till rätt spelare
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
            club_name = extract_club_name(match['team_name'])
            target_player_id = club_player_mapping.get(club_name)

            if target_player_id and target_player_id != player_id:
                # Skapa mapping från original till klubb-specifik spelare
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
                    f"{player_name} ({club_name})",
                    f"Multiclub fix for {match['season']}",
                    95,
                    "Multiclub separation: same name, different clubs",
                    f"Split {player_name} into club-specific players"
                ))
                mappings_created += 1

        conn.commit()
        print(f"\nSkapade {mappings_created} mappningar för {player_name}")

        return club_player_mapping

def verify_fix(original_player_id, player_name):
    """Verify that the fix worked correctly"""
    print(f"\n=== VERIFIERAR FIX FÖR {player_name} ===")

    with sqlite3.connect("goldenstat.db") as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Hitta alla relaterade spelare
        cursor.execute("SELECT id, name FROM players WHERE name LIKE ?", (f"%{player_name.split('(')[0].strip()}%",))
        related_players = cursor.fetchall()

        print("Relaterade spelare efter fix:")
        for player in related_players:
            # Räkna matcher för varje spelare (inklusive mappningar)
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
            print(f"  ID {player['id']}: {player['name']} - {total} matcher ({direct} direkta + {mapped} mappade)")

def main():
    print("=== MULTICLUB PLAYER FIXER ===")

    # Steg 1: Hitta verkliga problem
    problems = find_real_multiclub_problems()

    if not problems:
        print("\nInga verkliga multiclub-problem hittade!")
        return

    # Steg 2: Gruppera problem per spelare
    player_problems = defaultdict(list)
    for problem in problems:
        player_problems[(problem['id'], problem['name'])].append(problem)

    # Steg 3: Fixa de värsta fallen först
    print(f"\n=== FIXAR DE VÄRSTA FALLEN ===")

    fixed_count = 0
    for (player_id, player_name), season_problems in list(player_problems.items())[:5]:  # Fixa första 5
        try:
            fix_specific_player(player_id, player_name, season_problems)
            verify_fix(player_id, player_name)
            fixed_count += 1
        except Exception as e:
            print(f"FEL vid fix av {player_name}: {e}")

    print(f"\n=== SLUTFÖRD ===")
    print(f"Fixade {fixed_count} spelare med multiclub-problem")
    print(f"Återstående problem: {len(player_problems) - fixed_count}")

if __name__ == "__main__":
    main()