#!/usr/bin/env python3
"""
Map Lito to Lito (Nacka Wermdö)
All Lito matches are from Nacka Wermdö context
"""
import sqlite3

def analyze_lito():
    """Analyze Lito vs Lito (Nacka Wermdö) before mapping"""
    print("=== ANALYZING LITO BEFORE MAPPING ===")

    with sqlite3.connect("../goldenstat.db") as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Get player IDs
        cursor.execute("SELECT id, name FROM players WHERE name LIKE '%Lito%'")
        players = cursor.fetchall()

        print("Found players:")
        player_mapping = {}
        for player in players:
            print(f"  {player['name']} (ID: {player['id']})")
            player_mapping[player['name']] = player['id']

        # Get match details
        for name, player_id in player_mapping.items():
            print(f"\n--- {name} (ID: {player_id}) ---")

            cursor.execute("""
                SELECT
                    m.season,
                    m.division,
                    t.name as team_name,
                    COUNT(*) as matches,
                    MIN(m.match_date) as first_match,
                    MAX(m.match_date) as last_match
                FROM sub_match_participants smp
                JOIN sub_matches sm ON smp.sub_match_id = sm.id
                JOIN matches m ON sm.match_id = m.id
                JOIN teams t ON (
                    CASE WHEN smp.team_number = 1 THEN m.team1_id ELSE m.team2_id END
                ) = t.id
                WHERE smp.player_id = ?
                GROUP BY m.season, m.division, t.name
                ORDER BY m.season, m.division
            """, (player_id,))

            contexts = cursor.fetchall()
            for ctx in contexts:
                print(f"  {ctx['team_name']} ({ctx['division']}) {ctx['season']}: {ctx['matches']} matches")
                print(f"    Period: {ctx['first_match'][:10]} to {ctx['last_match'][:10]}")

        return player_mapping

def apply_lito_mapping(player_mapping):
    """Apply Lito mapping"""

    # Find both variations
    short_name = None
    full_name = None

    for name, player_id in player_mapping.items():
        if name == "Lito":
            short_name = player_id
        elif "Nacka" in name:
            full_name = player_id

    if not short_name:
        print("ERROR: Could not find Lito player")
        return False

    if not full_name:
        print("WARNING: Lito (Nacka Wermdö) does not exist, creating it")
        with sqlite3.connect("../goldenstat.db") as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO players (name) VALUES (?)", ("Lito (Nacka Wermdö)",))
            full_name = cursor.lastrowid
            conn.commit()
            print(f"Created Lito (Nacka Wermdö) with ID: {full_name}")

    # Map short name to full name
    source_player_id = short_name     # "Lito"
    target_player_id = full_name      # "Lito (Nacka Wermdö)"
    canonical_name = "Lito (Nacka Wermdö)"

    print(f"\n=== APPLYING MAPPING ===")
    print(f"Source: 'Lito' (ID: {source_player_id})")
    print(f"Target: 'Lito (Nacka Wermdö)' (ID: {target_player_id})")
    print(f"Canonical: {canonical_name}")

    with sqlite3.connect("../goldenstat.db") as conn:
        cursor = conn.cursor()

        # Get sub-matches for source player that are NOT already mapped
        cursor.execute("""
            SELECT DISTINCT smp.sub_match_id,
                   t.name as team_name,
                   m.season,
                   m.division
            FROM sub_match_participants smp
            JOIN sub_matches sm ON smp.sub_match_id = sm.id
            JOIN matches m ON sm.match_id = m.id
            JOIN teams t ON (
                CASE WHEN smp.team_number = 1 THEN m.team1_id ELSE m.team2_id END
            ) = t.id
            WHERE smp.player_id = ?
            AND smp.sub_match_id NOT IN (
                SELECT sub_match_id
                FROM sub_match_player_mappings
                WHERE original_player_id = ?
            )
        """, (source_player_id, source_player_id))

        sub_matches = cursor.fetchall()
        print(f"Found {len(sub_matches)} sub-matches to map")

        # Apply mappings
        mapped_count = 0
        for sub_match in sub_matches:
            sub_match_id = sub_match[0]
            team_name = sub_match[1]
            season = sub_match[2]
            division = sub_match[3]

            match_context = f"{team_name} ({division}) {season}"

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
                sub_match_id,
                source_player_id,
                target_player_id,
                canonical_name,
                match_context,
                100,
                "Club context mapping - all Lito matches are from Nacka Wermdö",
                "Mapping Lito -> Lito (Nacka Wermdö)"
            ))
            mapped_count += 1

        conn.commit()
        print(f"Applied {mapped_count} new mappings")

        # Verify total mappings
        cursor.execute("""
            SELECT COUNT(*)
            FROM sub_match_player_mappings
            WHERE original_player_id = ? AND correct_player_id = ?
        """, (source_player_id, target_player_id))

        verified_count = cursor.fetchone()[0]
        print(f"Total mappings in database: {verified_count}")

        return True

def main():
    print("=== LITO MAPPING ===")

    # Analyze
    player_mapping = analyze_lito()

    # Apply mapping
    success = apply_lito_mapping(player_mapping)

    if success:
        print("\nLito mapping completed successfully!")
    else:
        print("\nLito mapping failed!")

if __name__ == "__main__":
    main()
