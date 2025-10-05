#!/usr/bin/env python3
"""
Fixa Petra från Sweden Capital matcherna med korrekt kontextuell mappning
"""
import sqlite3

def fix_petra_sweden_capital():
    """Fixa Petra från Sweden Capital med kontextuell mappning"""
    print("=== FIXA PETRA SWEDEN CAPITAL MAPPNINGAR ===")

    with sqlite3.connect("goldenstat.db") as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Hitta Petra (förnamn) spelare
        cursor.execute("SELECT id, name FROM players WHERE name = 'Petra'")
        petra_player = cursor.fetchone()

        if not petra_player:
            print("Ingen 'Petra' spelare hittad")
            return

        petra_id = petra_player['id']
        print(f"Petra spelare: ID {petra_id}")

        # Hitta alla Petra matcher från Sweden Capital som inte är mappade
        cursor.execute("""
            SELECT
                sm.id as sub_match_id,
                m.match_date,
                CASE WHEN smp.team_number = 1 THEN t1.name ELSE t2.name END as team_name,
                m.division
            FROM sub_match_participants smp
            JOIN sub_matches sm ON smp.sub_match_id = sm.id
            JOIN matches m ON sm.match_id = m.id
            JOIN teams t1 ON m.team1_id = t1.id
            JOIN teams t2 ON m.team2_id = t2.id
            WHERE smp.player_id = ?
              AND (t1.name LIKE '%Sweden%Capital%' OR t2.name LIKE '%Sweden%Capital%')
              AND sm.id NOT IN (
                  SELECT sub_match_id FROM sub_match_player_mappings
                  WHERE original_player_id = ?
              )
            ORDER BY m.match_date DESC
        """, (petra_id, petra_id))

        unmapped_sweden_matches = cursor.fetchall()
        print(f"Hittade {len(unmapped_sweden_matches)} omappade Sweden Capital matcher:")

        for match in unmapped_sweden_matches:
            print(f"  {match['match_date'][:10]}: {match['team_name']} (sub_match: {match['sub_match_id']})")

        if not unmapped_sweden_matches:
            print("Inga omappade Sweden Capital matcher hittades")
            return

        # Skapa/hitta Petra (Sweden Capital) spelare
        target_name = "Petra (Sweden Capital)"
        cursor.execute("SELECT id, name FROM players WHERE name = ?", (target_name,))
        target_player = cursor.fetchone()

        if not target_player:
            # Skapa ny spelare
            cursor.execute("INSERT INTO players (name) VALUES (?)", (target_name,))
            target_player_id = cursor.lastrowid
            print(f"Skapade ny spelare: {target_name} (ID: {target_player_id})")
        else:
            target_player_id = target_player['id']
            print(f"Hittade befintlig spelare: {target_name} (ID: {target_player_id})")

        # Skapa mappningar för alla omappade Sweden Capital matcher
        mappings_created = 0
        for match in unmapped_sweden_matches:
            cursor.execute("""
                INSERT INTO sub_match_player_mappings (
                    sub_match_id,
                    original_player_id,
                    correct_player_id,
                    correct_player_name,
                    confidence,
                    mapping_reason,
                    notes
                ) VALUES (?, ?, ?, ?, 90, 'Post-import contextual mapping', ?)
            """, (
                match['sub_match_id'],
                petra_id,
                target_player_id,
                target_name,
                f'Retroactive contextual mapping: Petra -> {target_name} for {match["team_name"]} match on {match["match_date"][:10]}'
            ))
            mappings_created += 1

        conn.commit()
        print(f"[OK] Skapade {mappings_created} kontextuella mappningar for Petra -> {target_name}")

        # Visa resultat
        cursor.execute("""
            SELECT
                COUNT(*) as total_mappings,
                MIN(sm.match_date) as first_match,
                MAX(sm.match_date) as last_match
            FROM sub_match_player_mappings smpm
            JOIN sub_matches sm ON smpm.sub_match_id = sm.id
            JOIN matches m ON sm.match_id = m.id
            WHERE smpm.original_player_id = ? AND smpm.correct_player_name = ?
        """, (petra_id, target_name))

        result = cursor.fetchone()
        if result['total_mappings']:
            print(f"Totalt har nu Petra {result['total_mappings']} mappningar till {target_name}")
            print(f"Datumspan: {result['first_match'][:10]} till {result['last_match'][:10]}")

if __name__ == "__main__":
    fix_petra_sweden_capital()