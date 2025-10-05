#!/usr/bin/env python3
"""
Map Johan Brink case variation
Super-safe candidate: same club (Oilers), no caution factors
Johan Brink (69 matches) vs Johan brink (10 matches)
"""
import sqlite3

def analyze_johan_brink_before_mapping():
    """Analyze Johan Brink vs Johan brink before mapping"""
    print("=== ANALYZING JOHAN BRINK BEFORE MAPPING ===")

    with sqlite3.connect("../goldenstat.db") as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Get player IDs and match info
        cursor.execute("SELECT id, name FROM players WHERE name IN ('Johan Brink', 'Johan brink')")
        players = cursor.fetchall()

        print("Found players:")
        player_mapping = {}
        for player in players:
            print(f"  {player['name']} (ID: {player['id']})")
            player_mapping[player['name']] = player['id']

        # Get detailed match info for both
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

def apply_johan_brink_mapping(player_mapping):
    """Apply the Johan Brink mapping"""

    # Determine source and target
    johan_upper_id = player_mapping.get("Johan Brink")
    johan_lower_id = player_mapping.get("Johan brink")

    if not johan_upper_id or not johan_lower_id:
        print("ERROR: Could not find both Johan Brink variations")
        return False

    # Use proper case as canonical
    source_player_id = johan_lower_id  # "Johan brink"
    target_player_id = johan_upper_id  # "Johan Brink"
    canonical_name = "Johan Brink"

    print(f"\n=== APPLYING MAPPING ===")
    print(f"Source: 'Johan brink' (ID: {source_player_id})")
    print(f"Target: 'Johan Brink' (ID: {target_player_id})")
    print(f"Canonical: {canonical_name}")

    with sqlite3.connect("../goldenstat.db") as conn:
        cursor = conn.cursor()

        # Get all sub-matches for source player
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
                "Case variation mapping - Oilers",
                95,
                "Safe case variation: same club, no temporal conflicts",
                "Super-safe candidate: Johan brink -> Johan Brink"
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
    print("=== JOHAN BRINK CASE VARIATION MAPPING ===")
    print("Super-safe candidate from analysis")

    # Step 1: Analyze before mapping
    player_mapping = analyze_johan_brink_before_mapping()

    # Step 2: Apply mapping
    success = apply_johan_brink_mapping(player_mapping)

    if success:
        print("\n✓ Johan Brink mapping completed successfully!")
    else:
        print("\n✗ Johan Brink mapping failed!")

if __name__ == "__main__":
    main()