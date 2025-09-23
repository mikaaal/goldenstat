#!/usr/bin/env python3
"""
Map Yannick Le Pauvre case variation
Nearly-safe candidate: same club (Dartanjang), 1 low/medium temporal conflict
Yannick Le Pauvre (60 matches) vs Yannick le Pauvre (34 matches)
"""
import sqlite3

def analyze_yannick_le_pauvre():
    """Analyze Yannick Le Pauvre vs Yannick le Pauvre before mapping"""
    print("=== ANALYZING YANNICK LE PAUVRE BEFORE MAPPING ===")

    with sqlite3.connect("../goldenstat.db") as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Get player IDs
        cursor.execute("SELECT id, name FROM players WHERE name LIKE 'Yannick%e Pauvre'")
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

def apply_yannick_mapping(player_mapping):
    """Apply Yannick Le Pauvre mapping"""

    # Find both variations
    proper_case = None
    lower_case = None

    for name, player_id in player_mapping.items():
        if name == "Yannick Le Pauvre":
            proper_case = player_id
        elif name == "Yannick le Pauvre":
            lower_case = player_id

    if not proper_case or not lower_case:
        print("ERROR: Could not find both Yannick variations")
        return False

    # Map lower case to proper case
    source_player_id = lower_case     # "Yannick le Pauvre"
    target_player_id = proper_case    # "Yannick Le Pauvre"
    canonical_name = "Yannick Le Pauvre"

    print(f"\n=== APPLYING MAPPING ===")
    print(f"Source: 'Yannick le Pauvre' (ID: {source_player_id})")
    print(f"Target: 'Yannick Le Pauvre' (ID: {target_player_id})")
    print(f"Canonical: {canonical_name}")

    with sqlite3.connect("../goldenstat.db") as conn:
        cursor = conn.cursor()

        # Get sub-matches for source player
        cursor.execute("""
            SELECT DISTINCT smp.sub_match_id
            FROM sub_match_participants smp
            WHERE smp.player_id = ?
        """, (source_player_id,))

        sub_matches = cursor.fetchall()
        print(f"Found {len(sub_matches)} sub-matches to map")

        # Apply mappings
        for sub_match in sub_matches:
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
                sub_match[0],
                source_player_id,
                target_player_id,
                canonical_name,
                "Case variation mapping - Dartanjang",
                90,
                "Nearly-safe case variation: same club, 1 low/medium temporal conflict",
                "Nearly-safe candidate: Yannick le Pauvre -> Yannick Le Pauvre"
            ))

        conn.commit()
        print(f"Applied {len(sub_matches)} mappings")

        # Verify
        cursor.execute("""
            SELECT COUNT(*)
            FROM sub_match_player_mappings
            WHERE original_player_id = ? AND correct_player_id = ?
        """, (source_player_id, target_player_id))

        verified_count = cursor.fetchone()[0]
        print(f"Verified: {verified_count} mappings in database")

        return verified_count == len(sub_matches)

def main():
    print("=== YANNICK LE PAUVRE CASE VARIATION MAPPING ===")

    # Analyze
    player_mapping = analyze_yannick_le_pauvre()

    # Apply mapping
    success = apply_yannick_mapping(player_mapping)

    if success:
        print("\nYannick Le Pauvre mapping completed successfully!")
    else:
        print("\nYannick Le Pauvre mapping failed!")

if __name__ == "__main__":
    main()