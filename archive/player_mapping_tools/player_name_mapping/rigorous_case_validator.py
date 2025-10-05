#!/usr/bin/env python3
"""
Rigorous Case Variation Validator
Uses the same strict validation criteria as Peter/Johan mappers:
- Same club required
- Temporal validation (no simultaneous play in different contexts)
- Clear separation or overlap patterns

Created: 2025-09-23
"""
import sqlite3
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from safe_name_resolver import SafeNameResolver
from datetime import datetime

def detailed_marcus_analysis():
    """Detailed analysis of Marcus Gavander vs Marcus gavander using strict criteria"""

    with sqlite3.connect("../goldenstat.db") as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        print("=== Rigorous Marcus Gavander Case Variation Analysis ===")

        # Get detailed match data for both players
        for player_name, player_id in [("Marcus Gavander", 278), ("Marcus gavander", 1798)]:
            print(f"\n--- {player_name} (ID: {player_id}) ---")

            cursor.execute("""
                SELECT
                    m.match_date,
                    m.season,
                    m.division,
                    t.name as team_name,
                    COUNT(*) as matches_on_date
                FROM sub_match_participants smp
                JOIN sub_matches sm ON smp.sub_match_id = sm.id
                JOIN matches m ON sm.match_id = m.id
                JOIN teams t ON (
                    CASE WHEN smp.team_number = 1 THEN m.team1_id ELSE m.team2_id END
                ) = t.id
                WHERE smp.player_id = ?
                GROUP BY m.match_date, m.season, m.division, t.name
                ORDER BY m.match_date
            """, (player_id,))

            matches = cursor.fetchall()
            print(f"Total match dates: {len(matches)}")

            # Group by season/division/team
            contexts = {}
            for match in matches:
                context_key = f"{match['team_name']} ({match['division']}) {match['season']}"
                if context_key not in contexts:
                    contexts[context_key] = {
                        'dates': [],
                        'match_count': 0
                    }
                contexts[context_key]['dates'].append(match['match_date'])
                contexts[context_key]['match_count'] += match['matches_on_date']

            print("Contexts:")
            for context, data in contexts.items():
                first_date = min(data['dates'])
                last_date = max(data['dates'])
                print(f"  {context}: {data['match_count']} matches ({first_date[:10]} to {last_date[:10]})")

def check_temporal_overlap_strict():
    """Check for strict temporal overlaps that would indicate different players"""

    with sqlite3.connect("../goldenstat.db") as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        print(f"\n=== Strict Temporal Overlap Analysis ===")

        # Get all match dates for both players
        cursor.execute("""
            SELECT
                p.name as player_name,
                p.id as player_id,
                m.match_date,
                m.season,
                m.division,
                t.name as team_name
            FROM sub_match_participants smp
            JOIN players p ON smp.player_id = p.id
            JOIN sub_matches sm ON smp.sub_match_id = sm.id
            JOIN matches m ON sm.match_id = m.id
            JOIN teams t ON (
                CASE WHEN smp.team_number = 1 THEN m.team1_id ELSE m.team2_id END
            ) = t.id
            WHERE p.id IN (278, 1798)  -- Marcus Gavander IDs
            ORDER BY m.match_date, p.name
        """)

        all_matches = cursor.fetchall()

        # Group by date to find same-day conflicts
        by_date = {}
        for match in all_matches:
            date = match['match_date'][:10]  # Just the date part
            if date not in by_date:
                by_date[date] = []
            by_date[date].append(match)

        conflicts = []
        for date, matches_on_date in by_date.items():
            if len(matches_on_date) > 1:
                # Check if both players played on same date
                players_on_date = set(m['player_name'] for m in matches_on_date)
                if len(players_on_date) > 1:
                    conflicts.append({
                        'date': date,
                        'matches': matches_on_date
                    })

        if conflicts:
            print(f"Found {len(conflicts)} dates with potential conflicts:")
            for conflict in conflicts:
                print(f"\n  Date: {conflict['date']}")
                for match in conflict['matches']:
                    print(f"    {match['player_name']}: {match['team_name']} ({match['division']}) {match['season']}")
        else:
            print("No same-date conflicts found")

def validate_marcus_mapping_safety():
    """Final validation using the same criteria as Peter/Johan mappers"""

    print(f"\n=== Final Safety Validation ===")

    # Apply the same business rules:
    # 1. Must be same club
    # 2. No simultaneous play in different divisions/contexts
    # 3. Clear temporal separation OR logical progression

    resolver = SafeNameResolver("../goldenstat.db")

    # Get contexts for both
    gavander_upper_contexts = resolver.get_player_contexts("Marcus Gavander")
    gavander_lower_contexts = resolver.get_player_contexts("Marcus gavander")

    print("Marcus Gavander contexts:")
    for ctx in gavander_upper_contexts:
        print(f"  {ctx.club_name} ({ctx.division}) {ctx.season}: {ctx.date_start} to {ctx.date_end}")

    print("Marcus gavander contexts:")
    for ctx in gavander_lower_contexts:
        print(f"  {ctx.club_name} ({ctx.division}) {ctx.season}: {ctx.date_start} to {ctx.date_end}")

    # Check rule 1: Same club?
    all_clubs = set()
    for ctx in gavander_upper_contexts + gavander_lower_contexts:
        all_clubs.add(ctx.club_name)

    print(f"\nClubs involved: {list(all_clubs)}")

    if len(all_clubs) == 1:
        print("✓ Rule 1 PASSED: Same club (Dartanjang)")
    else:
        print("✗ Rule 1 FAILED: Different clubs - likely different players")
        return False

    # Check rule 2: Temporal conflicts
    all_contexts = gavander_upper_contexts + gavander_lower_contexts
    conflicts = resolver.detect_temporal_conflicts(all_contexts)

    high_severity_conflicts = [c for c in conflicts if c.severity == 'high']
    if high_severity_conflicts:
        print("✗ Rule 2 FAILED: High severity temporal conflicts")
        return False
    else:
        print("✓ Rule 2 PASSED: No high-severity conflicts")

    # Check rule 3: Logical progression
    # Look for clear patterns that suggest same player vs different players
    print(f"\nTemporal pattern analysis:")

    # Sort all contexts by date
    all_contexts_sorted = sorted(all_contexts, key=lambda x: x.date_start or "")

    for i, ctx in enumerate(all_contexts_sorted):
        player_indicator = "Upper" if any(c.player_id == ctx.player_id for c in gavander_upper_contexts) else "Lower"
        print(f"  {i+1}. {ctx.season} {ctx.division}: {ctx.date_start} to {ctx.date_end} ({player_indicator})")

    # Final decision
    print(f"\n=== FINAL DECISION ===")
    can_merge, reason = resolver.can_safely_merge_contexts(all_contexts)

    if can_merge:
        print(f"✓ SAFE TO MERGE: {reason}")
        print("The case variation mapping is valid based on:")
        print("  - Same club (Dartanjang)")
        print("  - No high-severity temporal conflicts")
        print("  - Logical progression of play")
        return True
    else:
        print(f"✗ NOT SAFE TO MERGE: {reason}")
        print("Should UNDO the mapping!")
        return False

def undo_marcus_mapping():
    """Undo the Marcus mapping if it's determined to be unsafe"""

    print(f"\n=== UNDOING MARCUS MAPPING ===")

    with sqlite3.connect("../goldenstat.db") as conn:
        cursor = conn.cursor()

        # Remove mappings
        cursor.execute("""
            DELETE FROM sub_match_player_mappings
            WHERE original_player_id = 1798 AND correct_player_id = 278
        """)

        rows_deleted = cursor.rowcount
        conn.commit()

        print(f"Removed {rows_deleted} mappings")
        return rows_deleted > 0

if __name__ == "__main__":
    # Step 1: Detailed analysis
    detailed_marcus_analysis()

    # Step 2: Check strict temporal overlaps
    check_temporal_overlap_strict()

    # Step 3: Final validation
    is_safe = validate_marcus_mapping_safety()

    if not is_safe:
        print(f"\nMapping is NOT safe - undoing...")
        undo_marcus_mapping()
    else:
        print(f"\nMapping is confirmed SAFE - keeping it")