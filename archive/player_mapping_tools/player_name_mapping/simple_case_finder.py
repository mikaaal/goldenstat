#!/usr/bin/env python3
"""
Simple Case Variation Finder - Without Unicode symbols
"""
import sqlite3
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from safe_name_resolver import SafeNameResolver
from collections import defaultdict

def find_marcus_variations():
    """Find Marcus case variations specifically"""
    with sqlite3.connect("../goldenstat.db") as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Find all Marcus players
        cursor.execute("""
            SELECT
                p.id,
                p.name,
                COUNT(DISTINCT smp.sub_match_id) as match_count
            FROM players p
            JOIN sub_match_participants smp ON p.id = smp.player_id
            WHERE LOWER(p.name) LIKE 'marcus%'
            GROUP BY p.id, p.name
            ORDER BY match_count DESC
        """)

        marcus_players = cursor.fetchall()
        print(f"Found {len(marcus_players)} Marcus players:")

        for player in marcus_players:
            print(f"  '{player['name']}' (ID: {player['id']}, {player['match_count']} matches)")

        # Group by lowercase name to find case variations
        by_lower = defaultdict(list)
        for player in marcus_players:
            by_lower[player['name'].lower()].append(player)

        print(f"\nCase variation groups:")
        variations_found = []

        for lower_name, players in by_lower.items():
            if len(players) > 1:
                print(f"\n'{lower_name}' has {len(players)} variations:")
                for p in players:
                    print(f"  '{p['name']}' ({p['match_count']} matches)")
                variations_found.append((lower_name, players))

        return variations_found

def analyze_marcus_gavander():
    """Specifically analyze Marcus Gavander vs Marcus gavander"""
    resolver = SafeNameResolver("../goldenstat.db")

    print(f"\n=== Analyzing Marcus Gavander vs Marcus gavander ===")

    # Get contexts for both variations
    gavander_upper = resolver.get_player_contexts("Marcus Gavander")
    gavander_lower = resolver.get_player_contexts("Marcus gavander")

    print(f"Marcus Gavander contexts: {len(gavander_upper)}")
    for ctx in gavander_upper:
        print(f"  {ctx.club_name} ({ctx.division}) {ctx.season}: {ctx.match_count} matches")

    print(f"Marcus gavander contexts: {len(gavander_lower)}")
    for ctx in gavander_lower:
        print(f"  {ctx.club_name} ({ctx.division}) {ctx.season}: {ctx.match_count} matches")

    # Check for temporal conflicts
    all_contexts = gavander_upper + gavander_lower
    conflicts = resolver.detect_temporal_conflicts(all_contexts)

    if conflicts:
        print(f"\nFound {len(conflicts)} temporal conflicts:")
        for conflict in conflicts:
            print(f"  Players {conflict.player1_id} vs {conflict.player2_id}")
            print(f"  Overlap: {conflict.overlap_start} to {conflict.overlap_end}")
            print(f"  Different clubs: {conflict.different_clubs}")
            print(f"  Severity: {conflict.severity}")
    else:
        print(f"\nNo temporal conflicts found - safe to merge!")

    # Check if safe to merge
    can_merge, reason = resolver.can_safely_merge_contexts(all_contexts)
    print(f"\nCan merge: {can_merge}")
    print(f"Reason: {reason}")

    if can_merge:
        canonical_name = resolver.find_best_canonical_name(all_contexts)
        print(f"Recommended canonical name: '{canonical_name}'")

        # Create mapping recommendation
        with sqlite3.connect("../goldenstat.db") as conn:
            cursor = conn.cursor()

            # Get player IDs
            cursor.execute("SELECT id FROM players WHERE name = 'Marcus Gavander'")
            gavander_upper_id = cursor.fetchone()[0]

            cursor.execute("SELECT id FROM players WHERE name = 'Marcus gavander'")
            gavander_lower_id = cursor.fetchone()[0]

            if canonical_name == "Marcus Gavander":
                source_id = gavander_lower_id
                target_id = gavander_upper_id
                source_name = "Marcus gavander"
            else:
                source_id = gavander_upper_id
                target_id = gavander_lower_id
                source_name = "Marcus Gavander"

            print(f"\nRecommended mapping:")
            print(f"  Source: '{source_name}' (ID: {source_id})")
            print(f"  Target: '{canonical_name}' (ID: {target_id})")
            print(f"  Confidence: 95")
            print(f"  Type: case_variation")

            return {
                'source_player_id': source_id,
                'target_player_id': target_id,
                'canonical_name': canonical_name,
                'confidence': 95,
                'mapping_type': 'case_variation',
                'reason': 'Case variation of same player name'
            }

    return None

def create_case_mapping(mapping):
    """Create the actual mapping in the database"""
    if not mapping:
        print("No mapping to create")
        return

    with sqlite3.connect("../goldenstat.db") as conn:
        cursor = conn.cursor()

        # Insert into sub_match_player_mappings for all sub-matches of the source player
        cursor.execute("""
            SELECT DISTINCT smp.sub_match_id
            FROM sub_match_participants smp
            WHERE smp.player_id = ?
        """, (mapping['source_player_id'],))

        sub_matches = cursor.fetchall()

        print(f"\nApplying mapping to {len(sub_matches)} sub-matches...")

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
                mapping['source_player_id'],
                mapping['target_player_id'],
                mapping['canonical_name'],
                "Case variation mapping",
                mapping['confidence'],
                mapping['reason'],
                "Mapped case variation using safe temporal validation"
            ))

        conn.commit()
        print(f"Applied {len(sub_matches)} mappings successfully!")

if __name__ == "__main__":
    print("=== Marcus Case Variation Analysis ===")

    # Find all Marcus variations
    variations = find_marcus_variations()

    # Specifically analyze Marcus Gavander
    if any('marcus gavander' in v[0] for v in variations):
        mapping = analyze_marcus_gavander()

        if mapping:
            response = input("\nApply this mapping? (y/n): ")
            if response.lower() == 'y':
                create_case_mapping(mapping)
            else:
                print("Mapping not applied")
        else:
            print("No safe mapping could be created")
    else:
        print("\nNo Marcus Gavander case variations found")