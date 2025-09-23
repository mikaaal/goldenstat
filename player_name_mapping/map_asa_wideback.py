#!/usr/bin/env python3
"""
Map Åsa Widebäck case variation
Åsa Widebäck vs Åsa widebäck
"""
import sqlite3

def analyze_asa_wideback():
    """Analyze Åsa Widebäck vs Åsa widebäck before mapping"""
    print("=== ANALYZING ÅSA WIDEBÄCK BEFORE MAPPING ===")

    with sqlite3.connect("../goldenstat.db") as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Get player IDs - using wildcard for special characters
        cursor.execute("SELECT id, name FROM players WHERE name LIKE '%sa %ideb%ck'")
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

def apply_asa_wideback_mapping(player_mapping):
    """Apply Åsa Widebäck mapping"""

    # Find both variations
    proper_case = None
    lower_case = None

    for name, player_id in player_mapping.items():
        # Check for proper case (has uppercase in surname)
        if "Widebäck" in name or "Wideb" in name and any(c.isupper() for c in name[4:]):
            proper_case = player_id
            proper_name = name
        # Check for lower case (no uppercase in surname)
        elif "wideb" in name and not any(c.isupper() for c in name[4:]):
            lower_case = player_id
            lower_name = name

    if not proper_case or not lower_case:
        print("ERROR: Could not find both Åsa Widebäck variations")
        print("Available players:", list(player_mapping.keys()))
        return False

    # Map lower case to proper case
    source_player_id = lower_case
    target_player_id = proper_case
    canonical_name = proper_name

    print(f"\n=== APPLYING MAPPING ===")
    print(f"Source: '{lower_name}' (ID: {source_player_id})")
    print(f"Target: '{proper_name}' (ID: {target_player_id})")
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
                "Case variation mapping",
                85,
                "Case variation: database search result",
                f"Candidate: {lower_name} -> {proper_name}"
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
    print("=== ÅSA WIDEBÄCK CASE VARIATION MAPPING ===")

    # Analyze
    player_mapping = analyze_asa_wideback()

    # Apply mapping
    success = apply_asa_wideback_mapping(player_mapping)

    if success:
        print("\nÅsa Widebäck mapping completed successfully!")
    else:
        print("\nÅsa Widebäck mapping failed!")

if __name__ == "__main__":
    main()