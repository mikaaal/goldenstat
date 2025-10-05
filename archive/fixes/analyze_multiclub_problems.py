#!/usr/bin/env python3
"""
Analyze multi-CLUB problems (different clubs, not just different teams within same club)
"""
import sqlite3
import re

def extract_club_name(team_name):
    """Extract club name from team name (remove division info)"""
    # Remove common division patterns
    patterns = [
        r'\s*\([^)]*\)$',  # Remove anything in parentheses at end
        r'\s*(SL\d+|DS|\d+[A-Z]+|\d+F[A-Z]+|Superligan)$',  # Remove division codes
    ]

    club = team_name
    for pattern in patterns:
        club = re.sub(pattern, '', club).strip()

    return club

def find_multiclub_problems():
    """Find players who play for multiple CLUBS (not just teams) in same season"""
    print("=== SPELARE SOM SPELAR FÖR FLERA KLUBBAR SAMTIDIGT ===")

    with sqlite3.connect("goldenstat.db") as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Hämta alla spelare med flera lag
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

        # Hitta spelare med flera klubbar
        multiclub_problems = []
        for (player_id, player_name, season), teams in player_seasons.items():
            clubs = set(team['club_name'] for team in teams)

            if len(clubs) > 1:  # Spelar för flera klubbar
                total_matches = sum(team['matches'] for team in teams)
                multiclub_problems.append({
                    'id': player_id,
                    'name': player_name,
                    'season': season,
                    'clubs': list(clubs),
                    'teams': teams,
                    'total_matches': total_matches,
                    'club_count': len(clubs)
                })

        # Sortera efter antal klubbar och matcher
        multiclub_problems.sort(key=lambda x: (x['club_count'], x['total_matches']), reverse=True)

        print(f"Hittade {len(multiclub_problems)} spelare/säsong med MULTICLUB-problem:")

        for i, problem in enumerate(multiclub_problems[:15], 1):
            print(f"\n{i}. ID {problem['id']}: {problem['name']} ({problem['season']})")
            print(f"   {problem['club_count']} klubbar, {problem['total_matches']} matcher")

            for club in problem['clubs']:
                club_teams = [t for t in problem['teams'] if t['club_name'] == club]
                club_matches = sum(t['matches'] for t in club_teams)
                team_names = [t['team_name'] for t in club_teams]
                print(f"   -> {club}: {club_matches} matcher ({', '.join(team_names)})")

        if len(multiclub_problems) > 15:
            print(f"\n... och {len(multiclub_problems) - 15} fler")

        return multiclub_problems

def find_multiteam_sameclub():
    """Find players with multiple teams in SAME club (these might be OK)"""
    print("\n=== SPELARE MED FLERA LAG I SAMMA KLUBB ===")

    with sqlite3.connect("goldenstat.db") as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("""
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
            ORDER BY team_count DESC, total_matches DESC
        """)

        multiteam_data = cursor.fetchall()

        # Filtrera bort multiclub-problem (bara samma klubb kvar)
        sameclub_problems = []
        for row in multiteam_data:
            teams = row['teams'].split(',')
            clubs = set(extract_club_name(team.strip()) for team in teams)

            if len(clubs) == 1:  # Bara en klubb
                sameclub_problems.append({
                    'id': row['id'],
                    'name': row['name'],
                    'season': row['season'],
                    'club': list(clubs)[0],
                    'team_count': row['team_count'],
                    'total_matches': row['total_matches'],
                    'teams': teams
                })

        print(f"Hittade {len(sameclub_problems)} spelare med flera lag i SAMMA klubb:")

        for i, problem in enumerate(sameclub_problems[:10], 1):
            print(f"\n{i}. ID {problem['id']}: {problem['name']} ({problem['season']})")
            print(f"   Klubb: {problem['club']}")
            print(f"   {problem['team_count']} lag, {problem['total_matches']} matcher")
            print(f"   Lag: {', '.join(problem['teams'][:3])}{'...' if len(problem['teams']) > 3 else ''}")

        if len(sameclub_problems) > 10:
            print(f"\n... och {len(sameclub_problems) - 10} fler")

        return sameclub_problems

def main():
    print("=== MULTICLUB VS MULTITEAM ANALYS ===")

    # Hitta verkliga problem (flera klubbar)
    multiclub = find_multiclub_problems()

    # Hitta acceptabla fall (flera lag, samma klubb)
    sameclub = find_multiteam_sameclub()

    print(f"\n=== SAMMANFATTNING ===")
    print(f"VERKLIGA PROBLEM (flera klubbar): {len(multiclub)}")
    print(f"ACCEPTABLA FALL (flera lag, samma klubb): {len(sameclub)}")
    print(f"TOTALT MULTILAG: {len(multiclub) + len(sameclub)}")

    print(f"\nPRIORITET: Fixa de {len(multiclub)} multiclub-problemen först!")

if __name__ == "__main__":
    main()