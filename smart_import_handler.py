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

            # 1. Exakt matchning
            cursor.execute("SELECT id, name FROM players WHERE name = ?", (incoming_name,))
            exact_match = cursor.fetchone()
            if exact_match:
                return {
                    'action': 'exact_match',
                    'player_id': exact_match['id'],
                    'player_name': exact_match['name'],
                    'confidence': 100,
                    'notes': 'Exact match found'
                }

            # 2. Klub-specifik matchning (för separerade spelare)
            # Försök hitta basnamnet case-insensitive
            base_name_match = None
            for base_name in self.separated_players.keys():
                if base_name.lower() == incoming_name.lower():
                    base_name_match = base_name
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