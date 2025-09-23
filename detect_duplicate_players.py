#!/usr/bin/env python3
"""
Detect players who might be duplicates based on:
1. Same name but different cases
2. Players who play for multiple teams simultaneously in same season
"""
import sqlite3
from collections import defaultdict

def find_case_variations():
    """Find players with same name but different cases"""
    print("=== SPELARE MED CASE-VARIATIONER ===")

    with sqlite3.connect("goldenstat.db") as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Hitta alla spelare grupperade per lowercase namn
        cursor.execute("""
            SELECT id, name, LOWER(name) as lower_name
            FROM players
            ORDER BY lower_name, name
        """)

        players = cursor.fetchall()

        # Gruppera per lowercase namn
        name_groups = defaultdict(list)
        for player in players:
            name_groups[player['lower_name']].append((player['id'], player['name']))

        # Hitta grupper med flera variationer
        case_duplicates = []
        for lower_name, variants in name_groups.items():
            if len(variants) > 1:
                case_duplicates.append((lower_name, variants))

        print(f"Hittade {len(case_duplicates)} namn med case-variationer:")
        for lower_name, variants in case_duplicates[:10]:  # Visa första 10
            print(f"\n'{lower_name}':")
            for player_id, name in variants:
                print(f"  ID {player_id}: '{name}'")

        if len(case_duplicates) > 10:
            print(f"... och {len(case_duplicates) - 10} fler")

        return case_duplicates

def find_multi_team_players():
    """Find players who play for multiple teams in same season"""
    print("\n=== SPELARE SOM SPELAR FÖR FLERA LAG SAMTIDIGT ===")

    with sqlite3.connect("goldenstat.db") as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Hitta spelare som spelar för flera lag i samma säsong
        cursor.execute("""
            SELECT
                p.id,
                p.name,
                m.season,
                COUNT(DISTINCT t.id) as team_count,
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
            ORDER BY team_count DESC, p.name
        """)

        multi_team = cursor.fetchall()

        print(f"Hittade {len(multi_team)} spelare/säsong kombinationer med flera lag:")
        for player in multi_team[:15]:  # Visa första 15
            print(f"\nID {player['id']}: {player['name']} ({player['season']})")
            print(f"  {player['team_count']} lag: {player['teams'][:100]}...")

        if len(multi_team) > 15:
            print(f"... och {len(multi_team) - 15} fler")

        return multi_team

def find_suspicious_names():
    """Find player names that might be the same person"""
    print("\n=== MISSTÄNKT IDENTISKA NAMN ===")

    with sqlite3.connect("goldenstat.db") as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Hitta namn som är mycket lika (samma förnamn och efternamn)
        cursor.execute("""
            SELECT id, name
            FROM players
            WHERE name LIKE '% %'  -- Har både för- och efternamn
            ORDER BY name
        """)

        players = cursor.fetchall()

        # Gruppera per "förnamn efternamn" (ignorera case och extra text)
        import re
        name_groups = defaultdict(list)

        for player in players:
            # Extrahera förnamn och efternamn (första två ord)
            name_parts = player['name'].strip().split()
            if len(name_parts) >= 2:
                base_name = f"{name_parts[0].lower()} {name_parts[1].lower()}"
                name_groups[base_name].append((player['id'], player['name']))

        # Hitta grupper med flera variationer
        suspicious = []
        for base_name, variants in name_groups.items():
            if len(variants) > 1:
                # Kontrollera om de verkligen är olika (inte bara case)
                unique_names = set(v[1].lower() for v in variants)
                if len(unique_names) > 1:
                    suspicious.append((base_name, variants))

        print(f"Hittade {len(suspicious)} misstänkta namngrupper:")
        for base_name, variants in suspicious[:10]:  # Visa första 10
            print(f"\n'{base_name}':")
            for player_id, name in variants:
                print(f"  ID {player_id}: '{name}'")

        if len(suspicious) > 10:
            print(f"... och {len(suspicious) - 10} fler")

        return suspicious

def analyze_specific_player(player_name):
    """Analyze a specific player for multi-team issues"""
    with sqlite3.connect("goldenstat.db") as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                p.id,
                p.name,
                t.name as team_name,
                m.season,
                COUNT(*) as matches,
                MIN(m.match_date) as first_match,
                MAX(m.match_date) as last_match
            FROM sub_match_participants smp
            JOIN sub_matches sm ON smp.sub_match_id = sm.id
            JOIN matches m ON sm.match_id = m.id
            JOIN players p ON smp.player_id = p.id
            JOIN teams t ON (
                CASE WHEN smp.team_number = 1 THEN m.team1_id ELSE m.team2_id END
            ) = t.id
            WHERE p.name LIKE ?
            GROUP BY p.id, p.name, t.name, m.season
            ORDER BY p.id, m.season, t.name
        """, (f"%{player_name}%",))

        return cursor.fetchall()

def main():
    print("=== DETEKTOR FÖR DUPLICERADE SPELARE ===")

    # Steg 1: Hitta case-variationer
    case_dupes = find_case_variations()

    # Steg 2: Hitta spelare med flera lag
    multi_team = find_multi_team_players()

    # Steg 3: Hitta misstänkta namn
    suspicious = find_suspicious_names()

    print(f"\n=== SAMMANFATTNING ===")
    print(f"Case-variationer: {len(case_dupes)}")
    print(f"Multi-team problem: {len(multi_team)}")
    print(f"Misstänkta namn: {len(suspicious)}")

    # Föreslå prioritet för manuell granskning
    print(f"\n=== PRIORITERADE PROBLEM ===")
    print("1. Spelare med flest lag i samma säsong (troliga duplikater)")
    print("2. Case-variationer av samma namn")
    print("3. Namn som verkar vara samma person men skrivs olika")

if __name__ == "__main__":
    main()