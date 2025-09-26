#!/usr/bin/env python3
"""
Debug match import - undersök vad som importerades vs vad som skulle importerats
"""
import sqlite3

def debug_specific_match():
    """Debug Mjölner vs Dartanjang match"""
    print("=== DEBUG AV MJOLNER VS DARTANJANG MATCH ===")

    with sqlite3.connect("goldenstat.db") as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Hitta matchen
        cursor.execute("""
            SELECT m.*,
                   t1.name as team1_name,
                   t2.name as team2_name
            FROM matches m
            JOIN teams t1 ON m.team1_id = t1.id
            JOIN teams t2 ON m.team2_id = t2.id
            WHERE (t1.name LIKE '%Mjölner%' AND t2.name LIKE '%Dartanjang%')
               OR (t2.name LIKE '%Mjölner%' AND t1.name LIKE '%Dartanjang%')
            AND DATE(m.match_date) = '2025-09-23'
        """)

        match = cursor.fetchone()
        if not match:
            print("Ingen Mjölner vs Dartanjang match hittades!")
            return

        print(f"Match ID: {match['id']}")
        print(f"Datum: {match['match_date']}")
        print(f"Team1: {match['team1_name']} (ID: {match['team1_id']})")
        print(f"Team2: {match['team2_name']} (ID: {match['team2_id']})")
        print(f"Resultat: {match['team1_score']}-{match['team2_score']}")
        print(f"URL: {match['match_url'] if 'match_url' in match.keys() else 'N/A'}")

        # Hitta sub-matches
        cursor.execute("""
            SELECT * FROM sub_matches WHERE match_id = ?
        """, (match['id'],))

        sub_matches = cursor.fetchall()
        print(f"\nSub-matches: {len(sub_matches)}")

        total_players = 0
        for sub in sub_matches:
            print(f"\nSub-match ID {sub['id']}: {sub['match_name']}")
            print(f"  Type: {sub['match_type']}")
            print(f"  Legs: {sub['team1_legs']}-{sub['team2_legs']}")

            # Hitta spelare för denna sub-match
            cursor.execute("""
                SELECT smp.*, p.name as player_name
                FROM sub_match_participants smp
                JOIN players p ON smp.player_id = p.id
                WHERE smp.sub_match_id = ?
                ORDER BY smp.team_number, p.name
            """, (sub['id'],))

            players = cursor.fetchall()
            print(f"  Spelare ({len(players)}):")

            team1_players = []
            team2_players = []

            for player in players:
                team_name = match['team1_name'] if player['team_number'] == 1 else match['team2_name']
                print(f"    Team {player['team_number']}: {player['player_name']} (ID: {player['player_id']}) - {team_name}")

                if player['team_number'] == 1:
                    team1_players.append(player['player_name'])
                else:
                    team2_players.append(player['player_name'])

            total_players += len(players)

            print(f"  {match['team1_name']}: {', '.join(team1_players)}")
            print(f"  {match['team2_name']}: {', '.join(team2_players)}")

        print(f"\nTotalt spelare importerade: {total_players}")

        # Kolla om det finns throws-data
        cursor.execute("""
            SELECT COUNT(*) as throw_count
            FROM throws t
            JOIN legs l ON t.leg_id = l.id
            JOIN sub_matches sm ON l.sub_match_id = sm.id
            WHERE sm.match_id = ?
        """, (match['id'],))

        throw_count = cursor.fetchone()['throw_count']
        print(f"Kast importerade: {throw_count}")

if __name__ == "__main__":
    debug_specific_match()