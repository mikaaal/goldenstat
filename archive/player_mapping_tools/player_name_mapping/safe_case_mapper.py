#!/usr/bin/env python3
"""
Safe Case Variation Mapper
NEVER applies mappings automatically - only analyzes and presents for manual approval.
Learned from previous mistakes: always require human verification.

Created: 2025-09-23
"""
import sqlite3
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from safe_name_resolver import SafeNameResolver
from collections import defaultdict

class SafeCaseMapper:
    def __init__(self, db_path="../goldenstat.db"):
        self.db_path = db_path
        self.resolver = SafeNameResolver(db_path)

    def find_all_case_variations(self, min_matches=5):
        """Find all case variations but DO NOT apply any mappings"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # Find case variations
            query = """
            SELECT
                p.id,
                p.name,
                LOWER(p.name) as lower_name,
                COUNT(DISTINCT smp.sub_match_id) as match_count
            FROM players p
            JOIN sub_match_participants smp ON p.id = smp.player_id
            WHERE LENGTH(p.name) > 3
                AND p.name NOT LIKE '%(%'  -- Skip contextual players
                AND p.name NOT LIKE '% %(%'  -- Skip already mapped players
            GROUP BY p.id, p.name, LOWER(p.name)
            HAVING COUNT(DISTINCT smp.sub_match_id) >= ?
            ORDER BY LOWER(p.name), p.name
            """

            cursor.execute(query, (min_matches,))
            all_players = cursor.fetchall()

            # Group by lowercase name
            by_lower_name = defaultdict(list)
            for player in all_players:
                by_lower_name[player['lower_name']].append(player)

            # Find actual case variations
            case_variations = []
            for lower_name, players in by_lower_name.items():
                if len(players) > 1:
                    unique_cases = set(p['name'] for p in players)
                    if len(unique_cases) > 1:
                        case_variations.append({
                            'lower_name': lower_name,
                            'variations': players,
                            'total_players': len(players),
                            'total_matches': sum(p['match_count'] for p in players)
                        })

            # Sort by total matches
            case_variations.sort(key=lambda x: x['total_matches'], reverse=True)
            return case_variations

    def analyze_case_variation_safely(self, variation_group, show_details=True):
        """Analyze a case variation group with safety checks - NO AUTO-MAPPING"""
        lower_name = variation_group['lower_name']
        variations = variation_group['variations']

        if show_details:
            print(f"\n=== Analyzing: '{lower_name}' ===")
            print(f"Found {len(variations)} case variations:")
            for var in variations:
                print(f"  '{var['name']}' (ID: {var['id']}, {var['match_count']} matches)")

        # Get detailed context for each variation
        all_contexts = []
        player_details = {}

        for var in variations:
            contexts = self.resolver.get_player_contexts(var['name'])
            all_contexts.extend(contexts)

            player_details[var['id']] = {
                'name': var['name'],
                'contexts': contexts,
                'total_matches': var['match_count']
            }

        # Safety Analysis
        analysis = {
            'safe_to_merge': False,
            'risk_level': 'HIGH',
            'reasons': [],
            'recommendation': 'DO NOT MAP',
            'player_details': player_details
        }

        # Check 1: Same club rule
        all_clubs = set()
        for ctx in all_contexts:
            all_clubs.add(ctx.club_name)

        if len(all_clubs) > 1:
            analysis['reasons'].append(f"DANGER: Different clubs involved: {list(all_clubs)}")
            analysis['risk_level'] = 'VERY HIGH'
        elif len(all_clubs) == 1:
            analysis['reasons'].append(f"OK: Same club: {list(all_clubs)[0]}")
        else:
            analysis['reasons'].append("UNCLEAR: No club information")

        # Check 2: Temporal conflicts
        conflicts = self.resolver.detect_temporal_conflicts(all_contexts)
        high_severity = [c for c in conflicts if c.severity == 'high']

        if high_severity:
            analysis['reasons'].append(f"DANGER: {len(high_severity)} high-severity temporal conflicts")
            analysis['risk_level'] = 'VERY HIGH'
        elif conflicts:
            low_medium = [c for c in conflicts if c.severity in ['low', 'medium']]
            analysis['reasons'].append(f"CAUTION: {len(low_medium)} low/medium temporal conflicts")
        else:
            analysis['reasons'].append("OK: No temporal conflicts")

        # Check 3: Activity patterns
        total_contexts = len(all_contexts)
        total_variations = len(variations)

        if total_contexts > total_variations * 3:  # Many contexts per variation
            analysis['reasons'].append("COMPLEX: Many different contexts - needs careful review")

        # Check 4: Similar activity levels
        match_counts = [var['match_count'] for var in variations]
        max_matches = max(match_counts)
        min_matches = min(match_counts)

        if max_matches > min_matches * 5:  # Very different activity levels
            analysis['reasons'].append(f"SUSPICIOUS: Very different activity levels: {max_matches} vs {min_matches}")
        elif max_matches > min_matches * 2:
            analysis['reasons'].append(f"CAUTION: Different activity levels: {max_matches} vs {min_matches}")
        else:
            analysis['reasons'].append(f"OK: Similar activity levels: {max_matches} vs {min_matches}")

        # Final risk assessment
        danger_reasons = len([r for r in analysis['reasons'] if r.startswith('DANGER')])
        caution_reasons = len([r for r in analysis['reasons'] if r.startswith('CAUTION')])
        ok_reasons = len([r for r in analysis['reasons'] if r.startswith('OK')])

        if danger_reasons > 0:
            analysis['risk_level'] = 'VERY HIGH'
            analysis['recommendation'] = 'DO NOT MAP - Likely different players'
        elif caution_reasons > ok_reasons:
            analysis['risk_level'] = 'HIGH'
            analysis['recommendation'] = 'MANUAL REVIEW REQUIRED - Uncertain'
        elif len(all_clubs) == 1 and not high_severity:
            analysis['risk_level'] = 'MEDIUM'
            analysis['recommendation'] = 'POSSIBLE TO MAP - But verify manually'
            analysis['safe_to_merge'] = True
        else:
            analysis['risk_level'] = 'HIGH'
            analysis['recommendation'] = 'MANUAL REVIEW REQUIRED'

        if show_details:
            print(f"\nSAFETY ANALYSIS:")
            print(f"  Risk Level: {analysis['risk_level']}")
            print(f"  Recommendation: {analysis['recommendation']}")
            print(f"  Reasons:")
            for reason in analysis['reasons']:
                print(f"    - {reason}")

        return analysis

    def generate_mapping_report(self, case_variations, top_n=20):
        """Generate a comprehensive report of potential mappings for manual review"""

        print(f"=== CASE VARIATION MAPPING REPORT ===")
        print(f"Found {len(case_variations)} groups with case variations")
        print(f"Analyzing top {min(top_n, len(case_variations))} by activity")
        print(f"\nIMPORTANT: NO MAPPINGS WILL BE APPLIED AUTOMATICALLY")
        print(f"All recommendations require manual verification\n")

        safe_candidates = []
        risky_candidates = []
        dangerous_candidates = []

        for i, var_group in enumerate(case_variations[:top_n]):
            print(f"\n{'='*60}")
            print(f"CANDIDATE {i+1}/{min(top_n, len(case_variations))}")

            analysis = self.analyze_case_variation_safely(var_group, show_details=True)

            if analysis['risk_level'] == 'VERY HIGH':
                dangerous_candidates.append((var_group, analysis))
            elif analysis['risk_level'] == 'HIGH':
                risky_candidates.append((var_group, analysis))
            else:
                safe_candidates.append((var_group, analysis))

        # Summary
        print(f"\n{'='*60}")
        print(f"SUMMARY REPORT")
        print(f"{'='*60}")
        print(f"Safe candidates (MEDIUM risk): {len(safe_candidates)}")
        print(f"Risky candidates (HIGH risk): {len(risky_candidates)}")
        print(f"Dangerous candidates (VERY HIGH risk): {len(dangerous_candidates)}")

        if safe_candidates:
            print(f"\nSAFE CANDIDATES FOR POTENTIAL MAPPING:")
            for var_group, analysis in safe_candidates:
                names = [v['name'] for v in var_group['variations']]
                print(f"  '{var_group['lower_name']}': {names} ({analysis['recommendation']})")

        print(f"\nNEXT STEPS:")
        print(f"1. Review safe candidates manually")
        print(f"2. For each candidate you want to map:")
        print(f"   - Verify same person by checking match history/performance")
        print(f"   - Apply mapping using dedicated script")
        print(f"3. NEVER batch-apply mappings")

        return {
            'safe': safe_candidates,
            'risky': risky_candidates,
            'dangerous': dangerous_candidates
        }

def main():
    """Main function - analysis only, NO automatic mapping"""
    mapper = SafeCaseMapper()

    print("=== SAFE CASE VARIATION FINDER ===")
    print("This tool will ONLY analyze and report - NO automatic mappings")

    # Find all case variations
    case_variations = mapper.find_all_case_variations(min_matches=5)

    if not case_variations:
        print("No case variations found with 5+ matches")
        return

    # Generate comprehensive report
    results = mapper.generate_mapping_report(case_variations, top_n=15)

    print(f"\nAnalysis complete. Review results above.")
    print(f"Remember: Human verification required for all mappings!")

if __name__ == "__main__":
    main()