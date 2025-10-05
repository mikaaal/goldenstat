#!/usr/bin/env python3
"""
Batch Case Variation Mapper
Handles 20 "easy" mappings at a time with manual approval for each candidate.

Created: 2025-09-23
"""
import sqlite3
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from safe_case_mapper import SafeCaseMapper

class BatchCaseMapper:
    def __init__(self, db_path="../goldenstat.db"):
        self.db_path = db_path
        self.safe_mapper = SafeCaseMapper(db_path)

    def get_easy_candidates(self, max_candidates=20):
        """Get the easiest/safest case variation candidates"""
        print("=== Finding Easy Case Variation Candidates ===")

        case_variations = self.safe_mapper.find_all_case_variations(min_matches=5)

        easy_candidates = []

        for var_group in case_variations:
            analysis = self.safe_mapper.analyze_case_variation_safely(var_group, show_details=False)

            # Only include MEDIUM risk candidates (safest ones)
            if analysis['risk_level'] == 'MEDIUM' and analysis['safe_to_merge']:
                # Add extra info for decision making
                variations = var_group['variations']

                candidate = {
                    'lower_name': var_group['lower_name'],
                    'variations': variations,
                    'analysis': analysis,
                    'total_matches': var_group['total_matches'],
                    'approved': False  # Will be set during manual review
                }

                easy_candidates.append(candidate)

        # Sort by total matches (most active first)
        easy_candidates.sort(key=lambda x: x['total_matches'], reverse=True)

        return easy_candidates[:max_candidates]

    def present_candidates_for_approval(self, candidates):
        """Present candidates one by one for manual approval"""
        print(f"\n=== MANUAL APPROVAL FOR {len(candidates)} CANDIDATES ===")
        print("Review each candidate carefully. Type 'y' to approve, 'n' to skip")
        print("Type 'q' to quit, 'details' to see full analysis")
        print("")

        approved_candidates = []

        for i, candidate in enumerate(candidates):
            variations = candidate['variations']
            names = [v['name'] for v in variations]
            match_counts = [v['match_count'] for v in variations]

            print(f"\n--- CANDIDATE {i+1}/{len(candidates)} ---")
            print(f"Names: {' vs '.join(names)}")
            print(f"Matches: {' vs '.join(map(str, match_counts))}")
            print(f"Risk: {candidate['analysis']['risk_level']}")
            print(f"Recommendation: {candidate['analysis']['recommendation']}")

            # Show key reasons
            reasons = candidate['analysis']['reasons']
            safe_reasons = [r for r in reasons if r.startswith('OK')]
            caution_reasons = [r for r in reasons if r.startswith('CAUTION')]

            if safe_reasons:
                print(f"Safe factors: {'; '.join(safe_reasons)}")
            if caution_reasons:
                print(f"Caution factors: {'; '.join(caution_reasons)}")

            while True:
                response = input(f"Approve mapping? (y/n/details/q): ").lower().strip()

                if response == 'y':
                    candidate['approved'] = True
                    approved_candidates.append(candidate)
                    print("✓ APPROVED")
                    break
                elif response == 'n':
                    print("✗ SKIPPED")
                    break
                elif response == 'details':
                    # Show full analysis
                    print("\nFULL ANALYSIS:")
                    self.safe_mapper.analyze_case_variation_safely(
                        {'lower_name': candidate['lower_name'], 'variations': variations},
                        show_details=True
                    )
                    continue
                elif response == 'q':
                    print("Quitting approval process...")
                    return approved_candidates
                else:
                    print("Please enter 'y', 'n', 'details', or 'q'")

        print(f"\n=== APPROVAL SUMMARY ===")
        print(f"Approved: {len(approved_candidates)}/{len(candidates)}")

        if approved_candidates:
            print("Approved mappings:")
            for candidate in approved_candidates:
                names = [v['name'] for v in candidate['variations']]
                print(f"  {' -> '.join(names)}")

        return approved_candidates

    def create_mapping_for_candidate(self, candidate):
        """Create mapping entries for a single candidate"""
        variations = candidate['variations']

        # Find canonical name (usually the one with proper casing)
        canonical_name = None
        canonical_player_id = None

        # Prefer the variation with more matches and proper casing
        best_variation = max(variations, key=lambda v: (v['match_count'], sum(1 for c in v['name'] if c.isupper())))
        canonical_name = best_variation['name']
        canonical_player_id = best_variation['id']

        mappings = []
        for var in variations:
            if var['id'] != canonical_player_id:
                mappings.append({
                    'source_player_id': var['id'],
                    'source_name': var['name'],
                    'target_player_id': canonical_player_id,
                    'target_name': canonical_name,
                    'confidence': 95,
                    'mapping_type': 'case_variation_batch',
                    'reason': f"Batch case variation mapping: {var['name']} -> {canonical_name}"
                })

        return mappings

    def apply_batch_mappings(self, approved_candidates):
        """Apply all approved mappings in a single batch"""
        if not approved_candidates:
            print("No approved candidates to process")
            return

        print(f"\n=== APPLYING {len(approved_candidates)} BATCH MAPPINGS ===")

        all_mappings = []

        # Generate all mappings first
        for candidate in approved_candidates:
            mappings = self.create_mapping_for_candidate(candidate)
            all_mappings.extend(mappings)

        if not all_mappings:
            print("No mappings to apply")
            return

        print(f"Generated {len(all_mappings)} individual mappings")

        # Show what will be applied
        print("\nMappings to apply:")
        for mapping in all_mappings:
            print(f"  '{mapping['source_name']}' -> '{mapping['target_name']}'")

        # Final confirmation
        response = input(f"\nApply all {len(all_mappings)} mappings? (y/n): ").lower()
        if response != 'y':
            print("Batch mapping cancelled")
            return

        # Apply to database
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            total_sub_matches_mapped = 0

            for mapping in all_mappings:
                # Get all sub-matches for the source player
                cursor.execute("""
                    SELECT DISTINCT smp.sub_match_id
                    FROM sub_match_participants smp
                    WHERE smp.player_id = ?
                """, (mapping['source_player_id'],))

                sub_matches = cursor.fetchall()

                # Apply mapping to each sub-match
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
                        mapping['target_name'],
                        "Batch case variation mapping",
                        mapping['confidence'],
                        mapping['reason'],
                        f"Batch processed: safe case variation"
                    ))

                total_sub_matches_mapped += len(sub_matches)
                print(f"  Mapped {len(sub_matches)} sub-matches for '{mapping['source_name']}'")

            conn.commit()

        print(f"\n✓ BATCH COMPLETE!")
        print(f"Applied {len(all_mappings)} player mappings")
        print(f"Mapped {total_sub_matches_mapped} total sub-matches")

        # Verification
        self.verify_batch_mappings(all_mappings)

    def verify_batch_mappings(self, mappings):
        """Verify that all mappings were applied correctly"""
        print(f"\n=== VERIFICATION ===")

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            total_verified = 0

            for mapping in mappings:
                cursor.execute("""
                    SELECT COUNT(*)
                    FROM sub_match_player_mappings
                    WHERE original_player_id = ? AND correct_player_id = ?
                """, (mapping['source_player_id'], mapping['target_player_id']))

                count = cursor.fetchone()[0]
                total_verified += count

                if count > 0:
                    print(f"✓ {mapping['source_name']} -> {mapping['target_name']}: {count} mappings")
                else:
                    print(f"✗ {mapping['source_name']} -> {mapping['target_name']}: NO MAPPINGS FOUND!")

        print(f"\nVerified {total_verified} total mappings in database")

def main():
    """Main batch processing function"""
    print("=== BATCH CASE VARIATION MAPPER ===")
    print("Processes up to 20 safe case variation mappings at a time")
    print("Requires manual approval for each candidate\n")

    mapper = BatchCaseMapper()

    # Step 1: Find easy candidates
    candidates = mapper.get_easy_candidates(max_candidates=20)

    if not candidates:
        print("No easy case variation candidates found")
        return

    print(f"Found {len(candidates)} easy candidates")

    # Step 2: Manual approval
    approved = mapper.present_candidates_for_approval(candidates)

    if not approved:
        print("No candidates approved for mapping")
        return

    # Step 3: Apply batch mappings
    mapper.apply_batch_mappings(approved)

if __name__ == "__main__":
    main()