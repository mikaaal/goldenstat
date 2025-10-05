#!/usr/bin/env python3
"""
Analyze players from specific match date
Fixed Unicode encoding issues for Windows console
"""
import sqlite3
import sys

def analyze_players_from_date(match_date="2025-09-23"):
    """Analyze all players from matches on specific date"""
    print(f"=== ANALYS AV SPELARE FRAN {match_date} ===")

    with sqlite3.connect("goldenstat.db") as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Hitta alla matcher från datumet
        cursor.execute("""
            SELECT id, match_date,
                   (SELECT name FROM teams WHERE id = team1_id) as team1,
                   (SELECT name FROM teams WHERE id = team2_id) as team2,
                   team1_score, team2_score
            FROM matches
            WHERE DATE(match_date) = ?
            ORDER BY match_date
        """, (match_date,))

        matches = cursor.fetchall()

        if not matches:
            print(f"Inga matcher hittades for {match_date}")
            return

        print(f"Hittade {len(matches)} matcher:")

        all_players = []

        for match in matches:
            print(f"\nMatch ID {match['id']}: {match['team1']} vs {match['team2']}")
            print(f"Resultat: {match['team1_score']}-{match['team2_score']}")
            print(f"Tid: {match['match_date']}")

            # Hitta alla spelare i denna match
            cursor.execute("""
                SELECT DISTINCT
                    p.id, p.name,
                    CASE WHEN smp.team_number = 1 THEN ? ELSE ? END as playing_for
                FROM sub_match_participants smp
                JOIN sub_matches sm ON smp.sub_match_id = sm.id
                JOIN players p ON smp.player_id = p.id
                WHERE sm.match_id = ?
                ORDER BY smp.team_number, p.name
            """, (match['team1'], match['team2'], match['id']))

            match_players = cursor.fetchall()

            print(f"Spelare ({len(match_players)}):")
            for player in match_players:
                player_info = f"  ID {player['id']}: {player['name']} ({player['playing_for']})"
                print(player_info)
                all_players.append({
                    'id': player['id'],
                    'name': player['name'],
                    'team': player['playing_for'],
                    'match_id': match['id']
                })

        # Sammanfattning av alla unika spelare
        unique_players = {}
        for player in all_players:
            if player['name'] not in unique_players:
                unique_players[player['name']] = []
            unique_players[player['name']].append(player['team'])

        print(f"\n=== SAMMANFATTNING ===")
        print(f"Totalt {len(all_players)} spelarinstanser")
        print(f"Unika spelare: {len(unique_players)}")

        for name, teams in unique_players.items():
            teams_str = ", ".join(set(teams))
            print(f"  {name} -> {teams_str}")

        # Kolla specifikt efter Mats Andersson och Micke Lundberg
        print(f"\n=== SOKNING EFTER SPECIFIKA SPELARE ===")
        target_names = ['Mats Andersson', 'Micke Lundberg']

        for target_name in target_names:
            cursor.execute("""
                SELECT DISTINCT p.name, p.id
                FROM players p
                WHERE p.name LIKE ?
                ORDER BY p.name
            """, (f"%{target_name}%",))

            variants = cursor.fetchall()
            print(f"\n{target_name} varianter i databasen:")

            if not variants:
                print(f"  Inga {target_name} spelare hittades!")
                continue

            for variant in variants:
                print(f"  ID {variant['id']}: {variant['name']}")

                # Kolla om denna variant spelade på detta datum
                cursor.execute("""
                    SELECT COUNT(*) as match_count
                    FROM sub_match_participants smp
                    JOIN sub_matches sm ON smp.sub_match_id = sm.id
                    JOIN matches m ON sm.match_id = m.id
                    WHERE smp.player_id = ? AND DATE(m.match_date) = ?
                """, (variant['id'], match_date))

                date_matches = cursor.fetchone()['match_count']
                if date_matches > 0:
                    print(f"    SPELADE {date_matches} matcher pa {match_date}")
                else:
                    print(f"    Spelade INTE pa {match_date}")

if __name__ == "__main__":
    analyze_players_from_date("2025-09-23")