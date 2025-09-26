#!/usr/bin/env python3
"""
Smart Import Handler för att hantera våra mappningar och separationer
"""
import sqlite3
import re
import unicodedata
from collections import defaultdict

class SmartPlayerMatcher:
    """Hanterar intelligent matchning av spelare vid import"""

    def __init__(self, db_path="goldenstat.db"):
        self.db_path = db_path
        self.separated_players = {}  # basnamn -> [klubb-varianter]
        self.mapped_players = {}     # original_namn -> correct_namn
        self.club_standardizer = {}  # klubb-variationer -> standard namn
        self._load_existing_mappings()

    def _load_existing_mappings(self):
        """Ladda alla befintliga mappningar och separationer"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # Ladda separerade spelare (multiclub-fixar)
            cursor.execute("""
                SELECT id, name
                FROM players
                WHERE name LIKE '% (%)'
                AND id >= 2314
            """)

            for player in cursor.fetchall():
                base_name = player['name'].split(' (')[0]
                club = player['name'].split(' (')[1].rstrip(')')

                if base_name not in self.separated_players:
                    self.separated_players[base_name] = []
                self.separated_players[base_name].append({
                    'id': player['id'],
                    'full_name': player['name'],
                    'club': club
                })

            # Ladda mappningar
            cursor.execute("""
                SELECT DISTINCT p1.name as original_name, smpm.correct_player_name
                FROM sub_match_player_mappings smpm
                JOIN players p1 ON smpm.original_player_id = p1.id
            """)

            for mapping in cursor.fetchall():
                self.mapped_players[mapping['original_name'].lower()] = mapping['correct_player_name']

        print(f"Laddade {len(self.separated_players)} separerade basnamn")
        print(f"Laddade {len(self.mapped_players)} mappningar")

    def standardize_club_name(self, team_name):
        """Standardisera klubbnamn (från tidigare logik)"""
        import unicodedata
        club = team_name

        # Remove division info
        patterns = [
            r'\s*\([^)]*\)$',
            r'\s*(SL\d+|DS|\d+[A-Z]+|\d+F[A-Z]+|Superligan)$',
        ]

        for pattern in patterns:
            club = re.sub(pattern, '', club).strip()

        # Unicode normalization
        club = unicodedata.normalize('NFKC', club)
        club = re.sub(r'[\u200b-\u200f\u2060\ufeff]', '', club)

        # Standardizations från tidigare
        standardizations = {
            'AIK': 'AIK Dart',
            'AIK Dart': 'AIK Dart',
            'AIK Dartförening': 'AIK Dart',
            'HMT Dart': 'HMT Dart',
            'Engelen': 'HMT Dart',
            'Spikkastarna B': 'SpikKastarna',
        }

        # Check for AIK variants first (case-insensitive)
        for standard_key, standard_value in standardizations.items():
            if club.lower() == standard_key.lower():
                return standard_value

        return standardizations.get(club, club)

    def normalize_player_name(self, player_name):
        """Normalisera spelarnamn"""
        # Unicode normalization
        name = unicodedata.normalize('NFKC', player_name).strip()

        # Remove zero-width spaces
        name = re.sub(r'[\u200b-\u200f\u2060\ufeff]', '', name)

        return name

    def extract_club_name(self, team_name):
        """Extract club name from 'Club (Division)' format"""
        if '(' in team_name:
            return team_name.split('(')[0].strip()
        return team_name.strip()

    def find_player_match(self, incoming_name, team_name=None):
        """
        Hitta matchning för inkommande spelare

        Returns:
            {
                'action': 'exact_match|club_specific|case_variation|create_mapping|create_new',
                'player_id': int or None,
                'player_name': str,
                'confidence': int (0-100),
                'notes': str
            }
        """
        incoming_name = self.normalize_player_name(incoming_name)
        club = self.standardize_club_name(team_name) if team_name else None

        result = {
            'action': 'create_new',
            'player_id': None,
            'player_name': incoming_name,
            'confidence': 0,
            'notes': 'No match found'
        }

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # 1. FÖRST: Case-variation detection (högsta prioritet)
            # Hitta alla spelare med samma namn case-insensitive
            cursor.execute("""
                SELECT id, name,
                       (SELECT COUNT(*) FROM sub_match_participants WHERE player_id = players.id) as match_count
                FROM players
                WHERE LOWER(name) = LOWER(?)
                ORDER BY match_count DESC
            """, (incoming_name,))

            case_variants = cursor.fetchall()

            if len(case_variants) > 1:
                # Multiple case variants found - prioritera den med flest matcher
                primary_variant = case_variants[0]  # Den med flest matcher

                # Kolla om inkommande namn är exakt samma som primär variant
                if incoming_name == primary_variant['name']:
                    return {
                        'action': 'exact_match',
                        'player_id': primary_variant['id'],
                        'player_name': primary_variant['name'],
                        'confidence': 100,
                        'notes': f'Primary variant with {primary_variant["match_count"]} matches'
                    }
                else:
                    # Inkommande namn är case-variant - ska mappas till primär
                    return {
                        'action': 'case_variation_mapping_needed',
                        'player_id': primary_variant['id'],
                        'player_name': primary_variant['name'],
                        'confidence': 95,
                        'notes': f'Case variant -> primary with {primary_variant["match_count"]} matches',
                        'target_variant': primary_variant['name'],
                        'incoming_variant': incoming_name
                    }

            elif len(case_variants) == 1:
                # Single exact match - MEN först kolla om det är ett förnamn med etablerade mappningar
                exact_match = case_variants[0]

                # Om det är bara ett förnamn (utan mellanslag) och har etablerade mappningar, prioritera dem
                if ' ' not in incoming_name and len(incoming_name) >= 3 and len(incoming_name) <= 15:
                    # Kolla om detta namn har etablerade förnamn-mappningar
                    cursor.execute("""
                        SELECT DISTINCT smpm.correct_player_name,
                               COUNT(*) as mapping_count,
                               -- Kolla om mappningen är för samma klubb-kontext
                               GROUP_CONCAT(DISTINCT
                                   CASE WHEN smp.team_number = 1 THEN t1.name ELSE t2.name END
                               ) as mapped_teams
                        FROM sub_match_player_mappings smpm
                        JOIN players p ON smpm.original_player_id = p.id
                        JOIN sub_matches sm ON smpm.sub_match_id = sm.id
                        JOIN matches m ON sm.match_id = m.id
                        JOIN teams t1 ON m.team1_id = t1.id
                        JOIN teams t2 ON m.team2_id = t2.id
                        JOIN sub_match_participants smp ON sm.id = smp.sub_match_id
                        WHERE p.name = ? AND smp.player_id = p.id
                        GROUP BY smpm.correct_player_name
                        ORDER BY mapping_count DESC
                    """, (incoming_name,))

                    first_name_mappings = cursor.fetchall()

                    if first_name_mappings:
                        # KRITISKT: Endast använd förnamn-mappningar för SAMMA LAG-KONTEXT
                        best_mapping = None
                        if team_name:
                            # Extrahera klubb från team_name
                            club_name = self.extract_club_name(team_name)

                            for mapping in first_name_mappings:
                                mapped_teams = mapping['mapped_teams'] or ''
                                # STRIKT matchning - klubben MÅSTE finnas i mapped_teams
                                if club_name.lower() in mapped_teams.lower():
                                    # EXTRA KONTROLL: Target-spelaren ska också vara logisk för detta lag
                                    target_name = mapping['correct_player_name']

                                    # Om target-spelaren har lag-kontext i namnet, ska den matcha vårt lag
                                    if '(' in target_name:
                                        # Extrahera lag från target-spelarens namn
                                        target_team = target_name.split('(')[1].rstrip(')')
                                        target_club = self.standardize_club_name(target_team)
                                        current_club = self.standardize_club_name(club_name)

                                        # Target-spelaren ska tillhöra samma lag som vi söker för
                                        if target_club.lower() != current_club.lower():
                                            print(f"    [SKIP] Skipping mapping {target_name} - belongs to {target_club}, not {current_club}")
                                            continue

                                    best_mapping = mapping
                                    break

                        # VIKTIGT: Endast returnera mappning om vi hittade EXAKT SAME LAG
                        if best_mapping:
                            return {
                                'action': 'first_name_mapping_found',
                                'player_id': None,
                                'player_name': best_mapping['correct_player_name'],
                                'confidence': 90,
                                'notes': f'Team context first name mapping: {incoming_name} -> {best_mapping["correct_player_name"]} (team: {club_name}, {best_mapping["mapping_count"]} mappings)',
                                'mapping_type': 'first_name',
                                'original_name': incoming_name
                            }

                        # Om ingen team-specifik mappning, INTE använda mappningar från andra lag
                        # Låt systemet hantera detta som 'create_new' istället

                    # INNAN exact match: Kolla om det är ett förnamn med separerade spelare
                    if team_name:
                        club_name = self.extract_club_name(team_name)

                        # Leta efter partiell match bland separerade spelare
                        base_name_match = None
                        for base_name in self.separated_players.keys():
                            if base_name.lower().startswith(incoming_name.lower() + ' '):
                                base_name_match = base_name
                                print(f"    [PARTIAL] Partial match: '{incoming_name}' matches base '{base_name}'")
                                break

                        if base_name_match:
                            # Försök hitta klubb-specifik variant
                            for variant in self.separated_players[base_name_match]:
                                if variant['club'].lower() == club_name.lower():
                                    return {
                                        'action': 'club_specific',
                                        'player_id': variant['id'],
                                        'player_name': variant['full_name'],
                                        'confidence': 95,
                                        'notes': f'Matched to separated player via partial name: {incoming_name} -> {variant["full_name"]} (club: {variant["club"]})'
                                    }

                                # Kolla också standardiserad matchning
                                standardized_variant_club = self.standardize_club_name(variant['club'])
                                standardized_current_club = self.standardize_club_name(club_name)
                                if standardized_variant_club.lower() == standardized_current_club.lower():
                                    return {
                                        'action': 'club_specific_standardized',
                                        'player_id': variant['id'],
                                        'player_name': variant['full_name'],
                                        'confidence': 93,
                                        'notes': f'Matched to separated player via partial name (standardized): {incoming_name} -> {variant["full_name"]} (club: {variant["club"]})'
                                    }

                # Om inget separerat match, returnera exact match
                return {
                    'action': 'exact_match',
                    'player_id': exact_match['id'],
                    'player_name': exact_match['name'],
                    'confidence': 100,
                    'notes': f'Exact match with {exact_match["match_count"]} matches'
                }

            # 2. Kolla befintliga förnamn-mappningar för fall där ingen exakt match finns
            # Om incoming_name är bara ett förnamn, kolla om det finns etablerade mappningar
            if ' ' not in incoming_name and len(incoming_name) >= 3 and len(incoming_name) <= 15:
                # Detta kan vara ett förnamn - kolla befintliga mappningar
                cursor.execute("""
                    SELECT DISTINCT p.name as original_name, smpm.correct_player_name,
                           COUNT(*) as mapping_count,
                           -- Kolla om mappningen är för samma klubb-kontext
                           GROUP_CONCAT(DISTINCT
                               CASE WHEN smp.team_number = 1 THEN t1.name ELSE t2.name END
                           ) as mapped_teams
                    FROM sub_match_player_mappings smpm
                    JOIN players p ON smpm.original_player_id = p.id
                    JOIN sub_matches sm ON smpm.sub_match_id = sm.id
                    JOIN matches m ON sm.match_id = m.id
                    JOIN teams t1 ON m.team1_id = t1.id
                    JOIN teams t2 ON m.team2_id = t2.id
                    JOIN sub_match_participants smp ON sm.id = smp.sub_match_id
                    WHERE p.name = ? AND smp.player_id = p.id
                    GROUP BY p.name, smpm.correct_player_name
                    ORDER BY mapping_count DESC
                """, (incoming_name,))

                first_name_mappings = cursor.fetchall()

                if first_name_mappings:
                    # Hitta den bästa mappningen baserat på klubb-kontext
                    best_mapping = None
                    if team_name:
                        # Prioritera mappningar som matchar klubb-kontexten
                        club_name = self.extract_club_name(team_name)
                        for mapping in first_name_mappings:
                            mapped_teams = mapping['mapped_teams'] or ''
                            if club_name.lower() in mapped_teams.lower():
                                # EXTRA KONTROLL: Target-spelaren ska också vara logisk för detta lag
                                target_name = mapping['correct_player_name']

                                # Om target-spelaren har lag-kontext i namnet, ska den matcha vårt lag
                                if '(' in target_name:
                                    # Extrahera lag från target-spelarens namn
                                    target_team = target_name.split('(')[1].rstrip(')')
                                    target_club = self.standardize_club_name(target_team)
                                    current_club = self.standardize_club_name(club_name)

                                    # Target-spelaren ska tillhöra samma lag som vi söker för
                                    if target_club.lower() != current_club.lower():
                                        print(f"    [SKIP] Skipping mapping {target_name} - belongs to {target_club}, not {current_club}")
                                        continue

                                best_mapping = mapping
                                break

                    # VIKTIGT: Endast returnera mappning om vi hittade EXAKT SAME LAG
                    if best_mapping:
                        return {
                            'action': 'first_name_mapping_found',
                            'player_id': None,
                            'player_name': best_mapping['correct_player_name'],
                            'confidence': 90,
                            'notes': f'Team context first name mapping: {incoming_name} -> {best_mapping["correct_player_name"]} (team: {club_name}, {best_mapping["mapping_count"]} mappings)',
                            'mapping_type': 'first_name',
                            'original_name': incoming_name
                        }

                    # Om ingen team-specifik mappning finns, låt systemet skapa ny spelare
                    # INTE använda mappningar från andra lag!

            # 3. Klub-specifik matchning (för separerade spelare)
            # Försök hitta basnamnet case-insensitive, eller partiell match om det är förnamn
            base_name_match = None

            # Först: Exakt match
            for base_name in self.separated_players.keys():
                if base_name.lower() == incoming_name.lower():
                    base_name_match = base_name
                    break

            # Om ingen exakt match och det verkar vara ett förnamn, sök partiella matches
            if not base_name_match and ' ' not in incoming_name and len(incoming_name) >= 3:
                for base_name in self.separated_players.keys():
                    # Kolla om base_name börjar med incoming_name (t.ex. "Mats Andersson" börjar med "Mats")
                    if base_name.lower().startswith(incoming_name.lower() + ' '):
                        base_name_match = base_name
                        print(f"    [PARTIAL] Partial match: '{incoming_name}' matches base '{base_name}'")
                        break

            if base_name_match and club:
                # Först, försök exakt matchning
                for variant in self.separated_players[base_name_match]:
                    if variant['club'].lower() == club.lower():
                        return {
                            'action': 'club_specific',
                            'player_id': variant['id'],
                            'player_name': variant['full_name'],
                            'confidence': 95,
                            'notes': f'Matched to club-specific variant: {variant["club"]}'
                        }

                # Sedan, försök standardiserad matchning (för AIK varianter etc)
                for variant in self.separated_players[base_name_match]:
                    standardized_variant_club = self.standardize_club_name(variant['club'])
                    if standardized_variant_club.lower() == club.lower():
                        return {
                            'action': 'club_specific_standardized',
                            'player_id': variant['id'],
                            'player_name': variant['full_name'],
                            'confidence': 93,
                            'notes': f'Matched via standardized club names: {club} -> {variant["club"]}'
                        }

                # Om klubb-specifik variant inte finns, föreslå skapande
                return {
                    'action': 'create_club_variant',
                    'player_id': None,
                    'player_name': f'{base_name_match} ({club})',
                    'confidence': 90,
                    'notes': f'Need to create new club variant for {club}'
                }

            # 3. Kolla befintliga mappningar först (högsta prioritet)
            if incoming_name.lower() in self.mapped_players:
                mapped_name = self.mapped_players[incoming_name.lower()]
                cursor.execute("SELECT id, name FROM players WHERE name = ?", (mapped_name,))
                mapped_player = cursor.fetchone()
                if mapped_player:
                    return {
                        'action': 'existing_mapping',
                        'player_id': mapped_player['id'],
                        'player_name': mapped_player['name'],
                        'confidence': 90,
                        'notes': f'Using existing mapping: {incoming_name} -> {mapped_name}'
                    }

            # 4. Case-insensitive sökning
            cursor.execute("SELECT id, name FROM players WHERE LOWER(name) = LOWER(?)", (incoming_name,))
            case_matches = cursor.fetchall()

            if len(case_matches) == 1:
                return {
                    'action': 'case_variation',
                    'player_id': case_matches[0]['id'],
                    'player_name': case_matches[0]['name'],
                    'confidence': 85,
                    'notes': f'Case variation: {incoming_name} -> {case_matches[0]["name"]}'
                }

            # 5. Hantera multipla case-matches med mappningar
            if len(case_matches) > 1:
                # Om det finns flera case-matches, prioritera den som har flest mappningar
                best_candidate = None
                best_mapping_count = -1

                for case_match in case_matches:
                    cursor.execute("""
                        SELECT COUNT(*) as mapping_count
                        FROM sub_match_player_mappings
                        WHERE correct_player_id = ?
                    """, (case_match['id'],))
                    mapping_count = cursor.fetchone()['mapping_count']

                    if mapping_count > best_mapping_count:
                        best_mapping_count = mapping_count
                        best_candidate = case_match

                if best_candidate:
                    return {
                        'action': 'case_variation_prioritized',
                        'player_id': best_candidate['id'],
                        'player_name': best_candidate['name'],
                        'confidence': 88,
                        'notes': f'Multiple case matches, selected: {incoming_name} -> {best_candidate["name"]} (has {best_mapping_count} mappings)'
                    }

            # 6. Bindestreck/mellanslag variation
            hyphen_version = incoming_name.replace(' ', '-')
            space_version = incoming_name.replace('-', ' ')

            for variant in [hyphen_version, space_version]:
                if variant != incoming_name:
                    cursor.execute("SELECT id, name FROM players WHERE name = ?", (variant,))
                    hyphen_match = cursor.fetchone()
                    if hyphen_match:
                        return {
                            'action': 'hyphen_space_variation',
                            'player_id': hyphen_match['id'],
                            'player_name': hyphen_match['name'],
                            'confidence': 80,
                            'notes': f'Hyphen/space variation: {incoming_name} -> {hyphen_match["name"]}'
                        }

        return result

    def create_mapping_if_needed(self, sub_match_id, original_player_id, target_player_id, target_name, reason):
        """Skapa mappning om den inte redan finns"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            cursor.execute("""
                INSERT OR IGNORE INTO sub_match_player_mappings (
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
                original_player_id,
                target_player_id,
                target_name,
                'Smart import handler',
                85,
                'Automatic import matching',
                reason
            ))

            conn.commit()
            return cursor.rowcount > 0

def demo_smart_matching():
    """Demo av smart matching"""
    print("=== SMART IMPORT HANDLER DEMO ===")

    matcher = SmartPlayerMatcher()

    # Testa olika scenarion
    test_cases = [
        # Klubb-specifik matchning
        ("Mats Andersson", "Dartanjang (2FB)"),
        ("Mats Andersson", "SSDC SL6"),
        ("Mats Andersson", "AIK Dart"),

        # Case-variation scenarios
        ("mats andersson", "SSDC SL6"),
        ("marcus gavander", "Dartanjang"),
        ("TOMMY LINDSTRÖM", "SpikKastarna"),

        # Bindestreck/mellanslag
        ("Lars Erik Renström", "TYO DC SL4"),
        ("Lars-Erik Renström", "TYO DC SL4"),

        # Existerande spelare som redan har separationer
        ("Robert Goth", "AIK Dart"),

        # Helt nya spelare
        ("Ny Spelare Som Inte Finns", "AC DC"),
    ]

    print("\\nTest av inkommande spelare:")
    for player_name, team_name in test_cases:
        result = matcher.find_player_match(player_name, team_name)

        print(f"\\n'{player_name}' från '{team_name}':")
        print(f"  Action: {result['action']}")
        print(f"  Target: {result['player_name']} (ID: {result['player_id']})")
        print(f"  Confidence: {result['confidence']}%")
        print(f"  Notes: {result['notes']}")

if __name__ == "__main__":
    demo_smart_matching()