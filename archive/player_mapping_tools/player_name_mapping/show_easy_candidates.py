#!/usr/bin/env python3
"""
Show Easy Case Variation Candidates
Lists the 20 safest candidates for you to review before mapping.

Created: 2025-09-23
"""
import sqlite3
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from safe_case_mapper import SafeCaseMapper

def show_all_easy_candidates():
    """Show all easy candidates for manual review"""
    print("=== 20 EASIEST CASE VARIATION CANDIDATES ===")
    print("These are the safest candidates based on our analysis")
    print("All have MEDIUM risk level and same club\n")

    mapper = SafeCaseMapper("../goldenstat.db")
    case_variations = mapper.find_all_case_variations(min_matches=5)

    easy_candidates = []

    for var_group in case_variations:
        analysis = mapper.analyze_case_variation_safely(var_group, show_details=False)

        if analysis['risk_level'] == 'MEDIUM' and analysis['safe_to_merge']:
            variations = var_group['variations']

            candidate = {
                'lower_name': var_group['lower_name'],
                'variations': variations,
                'analysis': analysis,
                'total_matches': var_group['total_matches']
            }

            easy_candidates.append(candidate)

    # Sort by total matches
    easy_candidates.sort(key=lambda x: x['total_matches'], reverse=True)

    print(f"Found {len(easy_candidates)} MEDIUM risk candidates:")
    print("=" * 80)

    for i, candidate in enumerate(easy_candidates[:20]):
        variations = candidate['variations']
        names = [v['name'] for v in variations]
        match_counts = [v['match_count'] for v in variations]

        # Get club info
        club_info = "Unknown club"
        for reason in candidate['analysis']['reasons']:
            if reason.startswith('OK: Same club:'):
                club_info = reason.replace('OK: Same club: ', '')
                break

        print(f"\n{i+1:2d}. {' vs '.join(names)}")
        print(f"    Matches: {' vs '.join(map(str, match_counts))} (total: {candidate['total_matches']})")
        print(f"    Club: {club_info}")
        print(f"    Risk: {candidate['analysis']['risk_level']}")

        # Show key factors
        reasons = candidate['analysis']['reasons']
        caution_reasons = [r for r in reasons if r.startswith('CAUTION')]
        if caution_reasons:
            print(f"    Caution: {'; '.join(caution_reasons)}")

    print("\n" + "=" * 80)
    print("NEXT STEPS:")
    print("1. Review the candidates above")
    print("2. Note down which ones you want to map (by number)")
    print("3. Use the batch mapper to apply selected mappings")
    print("4. Or manually create specific mapping scripts for individual candidates")

    print(f"\nEXAMPLE SAFE CANDIDATES TO START WITH:")
    for i, candidate in enumerate(easy_candidates[:5]):
        names = [v['name'] for v in candidate['variations']]
        print(f"  {i+1}. {' -> '.join(names)}")

if __name__ == "__main__":
    show_all_easy_candidates()