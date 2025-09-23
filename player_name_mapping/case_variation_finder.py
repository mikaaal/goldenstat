#!/usr/bin/env python3
"""
Case Variation Finder
Identifies players with same name but different case variations (e.g. Marcus Gavander vs Marcus gavander)
Uses the same temporal validation logic as other mappers.

Created: 2025-09-23
"""
import sqlite3
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from safe_name_resolver import SafeNameResolver
from collections import defaultdict

class CaseVariationFinder:
    def __init__(self, db_path="../goldenstat.db"):
        self.db_path = db_path
        self.resolver = SafeNameResolver(db_path)

    def find_case_variations(self, min_matches=5):
        """Find all players with case variations of the same name"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # Get all players with their match counts, grouped by lowercase name
            query = """
            SELECT
                p.id,
                p.name,
                LOWER(p.name) as lower_name,
                COUNT(DISTINCT smp.sub_match_id) as match_count
            FROM players p
            JOIN sub_match_participants smp ON p.id = smp.player_id
            WHERE LENGTH(p.name) > 3  -- Skip very short names
                AND p.name NOT LIKE '%(%'  -- Skip contextual players like "Johan (Oilers)"
            GROUP BY p.id, p.name, LOWER(p.name)
            HAVING COUNT(DISTINCT smp.sub_match_id) >= ?
            ORDER BY LOWER(p.name), p.name
            """

            cursor.execute(query, (min_matches,))
            all_players = cursor.fetchall()

            # Group by lowercase name to find variations
            by_lower_name = defaultdict(list)
            for player in all_players:
                by_lower_name[player['lower_name']].append(player)

            # Find groups with multiple case variations
            case_variations = []
            for lower_name, players in by_lower_name.items():
                if len(players) > 1:
                    # Check if they're actually different case variations
                    unique_cases = set(p['name'] for p in players)
                    if len(unique_cases) > 1:
                        case_variations.append({
                            'lower_name': lower_name,
                            'variations': players,
                            'total_players': len(players),
                            'total_matches': sum(p['match_count'] for p in players)
                        })

            # Sort by total matches (most active first)
            case_variations.sort(key=lambda x: x['total_matches'], reverse=True)

            return case_variations

    def analyze_case_variation_group(self, variation_group):
        """Analyze a specific case variation group for temporal conflicts"""
        lower_name = variation_group['lower_name']
        variations = variation_group['variations']

        print(f"\n=== Analyzing case variations for '{lower_name}' ===")
        print(f"Found {len(variations)} variations:")
        for var in variations:
            print(f"  '{var['name']}' (ID: {var['id']}, {var['match_count']} matches)")

        # Get contexts for all variations
        all_contexts = []
        for var in variations:
            contexts = self.resolver.get_player_contexts(var['name'])
            all_contexts.extend(contexts)

        # Check for temporal conflicts
        conflicts = self.resolver.detect_temporal_conflicts(all_contexts)

        if conflicts:
            print(f"\n  ⚠ Found {len(conflicts)} temporal conflicts:")
            for conflict in conflicts:
                print(f"    Player {conflict.player1_id} vs {conflict.player2_id}: {conflict.severity} severity")
                print(f"      Overlap: {conflict.overlap_start} to {conflict.overlap_end}")
                if conflict.different_clubs:
                    print(f"      Different clubs - likely different people")
                else:
                    print(f"      Same club - likely same person with case variation")
        else:
            print(f"  ✓ No temporal conflicts found")

        # Determine if safe to merge
        can_merge, reason = self.resolver.can_safely_merge_contexts(all_contexts)

        if can_merge:
            # Find the best canonical name
            canonical_name = self.resolver.find_best_canonical_name(all_contexts)

            print(f"  ✓ Safe to merge - canonical name: '{canonical_name}'")

            # Create mapping recommendations
            mappings = []
            canonical_player_id = None

            # Find the player ID for the canonical name
            for var in variations:
                if var['name'] == canonical_name:
                    canonical_player_id = var['id']
                    break

            if canonical_player_id:
                for var in variations:
                    if var['id'] != canonical_player_id:
                        mappings.append({
                            'source_player_id': var['id'],
                            'source_name': var['name'],
                            'target_player_id': canonical_player_id,
                            'target_name': canonical_name,
                            'confidence': 95,
                            'mapping_type': 'case_variation',
                            'reason': f"Case variation of '{canonical_name}'"
                        })

                print(f"  → Recommended mappings: {len(mappings)}")
                for mapping in mappings:
                    print(f"    '{mapping['source_name']}' → '{mapping['target_name']}'")

            return mappings
        else:
            print(f"  ✗ Cannot merge: {reason}")
            return []

    def find_specific_case_variation(self, name_pattern):
        """Find case variations for a specific name pattern"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # Search for names matching the pattern (case insensitive)
            cursor.execute("""
                SELECT
                    p.id,
                    p.name,
                    COUNT(DISTINCT smp.sub_match_id) as match_count
                FROM players p
                JOIN sub_match_participants smp ON p.id = smp.player_id
                WHERE LOWER(p.name) LIKE LOWER(?)
                GROUP BY p.id, p.name
                ORDER BY match_count DESC
            """, (f"%{name_pattern}%",))

            results = cursor.fetchall()

            if not results:
                print(f"No players found matching '{name_pattern}'")
                return []

            print(f"Found {len(results)} players matching '{name_pattern}':")
            for player in results:
                print(f"  '{player['name']}' (ID: {player['id']}, {player['match_count']} matches)")

            # Group by lowercase name
            by_lower = defaultdict(list)
            for player in results:
                by_lower[player['name'].lower()].append(player)

            # Find actual case variations
            variations = []
            for lower_name, players in by_lower.items():
                if len(players) > 1:
                    variations.append({
                        'lower_name': lower_name,
                        'variations': players,
                        'total_players': len(players),
                        'total_matches': sum(p['match_count'] for p in players)
                    })

            return variations

def main():
    """Main function to find and analyze case variations"""
    finder = CaseVariationFinder()

    if len(sys.argv) > 1:
        # Search for specific name
        name_pattern = sys.argv[1]
        print(f"=== Searching for case variations of '{name_pattern}' ===")
        variations = finder.find_specific_case_variation(name_pattern)

        if variations:
            for var_group in variations:
                mappings = finder.analyze_case_variation_group(var_group)
        else:
            print(f"No case variations found for '{name_pattern}'")
    else:
        # Find all case variations
        print("=== Finding all case variation duplicates ===")

        case_variations = finder.find_case_variations(min_matches=5)

        print(f"Found {len(case_variations)} groups with case variations:")

        # Show summary
        for i, var_group in enumerate(case_variations[:10]):  # Show top 10
            lower_name = var_group['lower_name']
            variations = var_group['variations']
            total_matches = var_group['total_matches']

            print(f"\n{i+1}. '{lower_name}' ({len(variations)} variations, {total_matches} total matches)")
            for var in variations:
                print(f"   '{var['name']}' ({var['match_count']} matches)")

        if len(case_variations) > 10:
            print(f"\n... and {len(case_variations) - 10} more groups")

        # Analyze top 5 for detailed analysis
        print(f"\n=== Detailed Analysis of Top 5 ===")
        all_mappings = []

        for var_group in case_variations[:5]:
            mappings = finder.analyze_case_variation_group(var_group)
            all_mappings.extend(mappings)

        print(f"\n=== Summary ===")
        print(f"Analyzed {min(5, len(case_variations))} case variation groups")
        print(f"Generated {len(all_mappings)} potential mappings")

        if all_mappings:
            print(f"\nRecommended mappings:")
            for mapping in all_mappings:
                print(f"  '{mapping['source_name']}' → '{mapping['target_name']}' (confidence: {mapping['confidence']})")

if __name__ == "__main__":
    main()