#!/usr/bin/env python3
"""
Smart Season Importer med integrerad SmartPlayerMatcher
Baserad på NewSeasonImporter men med intelligent spelarmappning
"""
import time
import sqlite3
from typing import List, Dict, Optional
from new_season_importer import NewSeasonImporter
from smart_import_handler import SmartPlayerMatcher
import datetime

class SmartSeasonImporter(NewSeasonImporter):
    """Season importer med automatisk intelligent spelarmappning"""

    def __init__(self, db_path: str = "goldenstat.db"):
        super().__init__(db_path)
        self.matcher = SmartPlayerMatcher(db_path)
        self.import_log = {
            "players_handled": [],
            "statistics": {
                "auto_matched_high_confidence": 0,
                "auto_matched_medium_confidence": 0,
                "auto_created_with_context": 0,
                "auto_created_new": 0,
                "total_players_processed": 0
            },
            "warnings": [],
            "errors": []
        }

    def normalize_player_name(self, name: str) -> str:
        """Normalisera spelarnamn för att förhindra case-variation dubletter"""
        if not name:
            return name

        # Trimma whitespace
        normalized = name.strip()

        # Hantera parenteser separat - leta efter mönstret "... (...)"
        if '(' in normalized and ')' in normalized:
            # Hitta första parentess-början och sista parentess-slut
            paren_start = normalized.find('(')
            paren_end = normalized.rfind(')')

            if paren_start < paren_end:
                # Dela upp i: före_parenteser + parenteser + efter_parenteser
                before_paren = normalized[:paren_start].strip()
                paren_content = normalized[paren_start+1:paren_end]
                after_paren = normalized[paren_end+1:].strip()

                # Normalisera varje del
                normalized_before = ' '.join(word.capitalize() for word in before_paren.split() if word)
                normalized_paren = ' '.join(word.capitalize() for word in paren_content.split() if word)
                normalized_after = ' '.join(word.capitalize() for word in after_paren.split() if word)

                # Sätt ihop igen
                result_parts = []
                if normalized_before:
                    result_parts.append(normalized_before)
                if normalized_paren:
                    result_parts.append(f"({normalized_paren})")
                if normalized_after:
                    result_parts.append(normalized_after)

                return ' '.join(result_parts)

        # Ingen parentess - standard titel-case
        words = normalized.split()
        normalized_words = [word.capitalize() for word in words if word]

        return ' '.join(normalized_words)

    def extract_club_name(self, team_name: str) -> str:
        """Extract club name from 'Club (Division)' format"""
        if not team_name:
            return ""
        if '(' in team_name:
            return team_name.split('(')[0].strip()
        return team_name.strip()

    def import_players_smart(self, sub_match_id: int, stats_data: List[Dict], team1_id: int, team2_id: int, team1_name: str = None, team2_name: str = None):
        """Import players med INTELLIGENT AUTOMATISK mappning - ersätter original import_players"""
        try:
            # Använd de riktiga teamnamnen från match_info (fallback till ID-lookup)
            if not team1_name:
                team1_name = self.get_team_name_by_id(team1_id)
            if not team2_name:
                team2_name = self.get_team_name_by_id(team2_id)

            for team_index, team_stats in enumerate(stats_data):
                team_number = team_index + 1
                team_name = team1_name if team_number == 1 else team2_name

                # Calculate player average
                all_score = team_stats.get('allScore', 0)
                all_darts = team_stats.get('allDarts', 0)
                player_avg = round((all_score / all_darts) * 3, 2) if all_darts > 0 else 0

                # Process each player with SMART MAPPING
                order = team_stats.get('order', [])
                if not order:  # Skippa om order är None eller tom lista
                    continue

                for player_info in order:
                    raw_player_name = player_info.get('oname', 'Unknown').strip()

                    if not raw_player_name or raw_player_name == 'Unknown':
                        continue

                    # Normalisera spelarnamnet för att förhindra case-variation dubletter
                    normalized_player_name = self.normalize_player_name(raw_player_name)

                    # 🧠 SMART PLAYER MATCHING - AUTOMATISK, GENERELL
                    final_player_id = self.get_smart_player_id(
                        normalized_player_name,
                        team_name,
                        sub_match_id
                    )

                    # Insert participant med smart-matched player
                    participant_data = {
                        'sub_match_id': sub_match_id,
                        'player_id': final_player_id,
                        'team_number': team_number,
                        'player_avg': player_avg
                    }

                    self.db.insert_sub_match_participant(participant_data)
                    self.import_log["statistics"]["total_players_processed"] += 1

        except Exception as e:
            error_msg = f"Error importing players for sub_match {sub_match_id}: {str(e)}"
            print(f"ERROR: {error_msg}")
            self.import_log["errors"].append(error_msg)

    def get_smart_player_id(self, raw_player_name: str, team_name: str, sub_match_id: int) -> int:
        """🧠 GENERELL INTELLIGENT SPELARMATCHNING - fungerar för ALLA spelare"""

        # Använd SmartPlayerMatcher
        mapping_result = self.matcher.find_player_match(raw_player_name, team_name)

        action = mapping_result['action']
        confidence = mapping_result['confidence']

        # 🎯 AUTOMATISKA BESLUT baserat på action och confidence (GENERELLA regler)

        # Specialhantering för case-variationer
        if action == 'case_variation_mapping_needed':
            # För intelligent import: använd target-spelaren direkt
            # SKAPA INTE dubbletter under import-processen
            target_player_id = mapping_result['player_id']

            self.log_player_action("AUTO_CASE_VARIATION_MATCHED", raw_player_name, mapping_result)
            self.import_log["statistics"]["auto_matched_high_confidence"] += 1
            return target_player_id

        elif action == 'first_name_mapping_found':
            # För intelligent import: använd target-spelaren direkt
            # SKAPA INTE dubbletter under import-processen
            target_player_name = mapping_result['player_name']

            # Hitta target player ID baserat på namn
            with sqlite3.connect(self.db.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id FROM players WHERE name = ?", (target_player_name,))
                target_result = cursor.fetchone()

                if target_result:
                    target_player_id = target_result[0]

                    self.log_player_action("AUTO_FIRST_NAME_MATCHED", raw_player_name, mapping_result)
                    self.import_log["statistics"]["auto_matched_high_confidence"] += 1
                    return target_player_id
                else:
                    # Target spelare finns inte - fallback till att skapa ny
                    self.import_log["warnings"].append(f"First name mapping target not found: {target_player_name}")

        elif confidence >= 90:
            # Hög confidence - använd direkt
            if mapping_result['player_id']:
                self.log_player_action("AUTO_ACCEPT_HIGH_CONFIDENCE", raw_player_name, mapping_result)
                self.import_log["statistics"]["auto_matched_high_confidence"] += 1
                return mapping_result['player_id']

        elif confidence >= 75:
            # Medium confidence - acceptera men logga varning
            if mapping_result['player_id']:
                self.log_player_action("AUTO_ACCEPT_MEDIUM_CONFIDENCE", raw_player_name, mapping_result)
                self.import_log["statistics"]["auto_matched_medium_confidence"] += 1

                warning = f"Medium confidence match: {raw_player_name} -> {mapping_result['player_name']} (confidence: {confidence})"
                self.import_log["warnings"].append(warning)
                return mapping_result['player_id']

        # FÖRNAMN-SPECIFIK LOGIK: Om det är ett förnamn utan bra match, skapa kontextuell mappning
        if (' ' not in raw_player_name and len(raw_player_name) >= 3 and len(raw_player_name) <= 15 and
            team_name and confidence < 90):

            club_name = self.extract_club_name(team_name)
            contextual_name = f"{raw_player_name} ({club_name})"

            # Skapa/hitta den kontextuella spelaren
            contextual_player_id = self.db.get_or_create_player(contextual_name)

            # Skapa mappning från förnamnet till den kontextuella spelaren
            source_player_id = self.db.get_or_create_player(raw_player_name)

            # Skapa mappning för denna sub-match
            self.create_contextual_first_name_mapping(
                sub_match_id,
                source_player_id,
                contextual_player_id,
                contextual_name,
                raw_player_name,
                club_name
            )

            self.log_player_action("AUTO_CREATE_CONTEXTUAL_MAPPING", raw_player_name, {
                'source_name': raw_player_name,
                'target_name': contextual_name,
                'club': club_name,
                'confidence': 85
            })
            self.import_log["statistics"]["auto_created_with_context"] += 1
            return contextual_player_id

        # Fallback: Skapa ny spelare
        # Kontrollera om vi behöver klubb-kontext eller inte
        if self.needs_club_context(raw_player_name, mapping_result):
            # Namn-konflikt upptäckt - använd klubb-kontext
            contextual_name = self.generate_contextual_player_name(raw_player_name, team_name)
            new_player_id = self.db.get_or_create_player(contextual_name)

            self.log_player_action("AUTO_CREATE_WITH_CONTEXT", raw_player_name, {
                'original_result': mapping_result,
                'created_name': contextual_name,
                'created_id': new_player_id,
                'reason': 'Name conflict detected'
            })

            self.import_log["statistics"]["auto_created_with_context"] += 1
        else:
            # Helt ny spelare - använd originalnamnet
            new_player_id = self.db.get_or_create_player(raw_player_name)

            self.log_player_action("AUTO_CREATE_NEW", raw_player_name, {
                'original_result': mapping_result,
                'created_name': raw_player_name,
                'created_id': new_player_id,
                'reason': 'Completely new player'
            })

            self.import_log["statistics"]["auto_created_new"] += 1

        return new_player_id

    def create_case_variation_mapping(self, sub_match_id, source_player_id, target_player_id, target_player_name, source_player_name):
        """Skapa case variation mapping enligt etablerat schema"""
        try:
            with sqlite3.connect(self.db.db_path) as conn:
                cursor = conn.cursor()

                # Kolla om mappning redan finns för denna sub-match och spelare
                cursor.execute("""
                    SELECT COUNT(*) FROM sub_match_player_mappings
                    WHERE sub_match_id = ? AND original_player_id = ?
                """, (sub_match_id, source_player_id))

                if cursor.fetchone()[0] > 0:
                    # Mappning finns redan - skippa
                    return

                # Skapa mappning enligt schema från guiden
                cursor.execute("""
                    INSERT INTO sub_match_player_mappings (
                        sub_match_id,
                        original_player_id,
                        correct_player_id,
                        correct_player_name,
                        confidence,
                        mapping_reason,
                        notes
                    ) VALUES (?, ?, ?, ?, 95, 'Case variation mapping', ?)
                """, (
                    sub_match_id,
                    source_player_id,
                    target_player_id,
                    target_player_name,
                    f'Auto-mapped: "{source_player_name}" -> "{target_player_name}"'
                ))

                conn.commit()

        except Exception as e:
            error_msg = f"Error creating case variation mapping: {str(e)}"
            print(f"ERROR: {error_msg}")
            self.import_log["errors"].append(error_msg)

    def create_first_name_mapping(self, sub_match_id, source_player_id, target_player_id, target_player_name, source_player_name):
        """Skapa first name mapping enligt etablerat schema"""
        try:
            with sqlite3.connect(self.db.db_path) as conn:
                cursor = conn.cursor()

                # Kolla om mappning redan finns för denna sub-match och spelare
                cursor.execute("""
                    SELECT COUNT(*) FROM sub_match_player_mappings
                    WHERE sub_match_id = ? AND original_player_id = ?
                """, (sub_match_id, source_player_id))

                if cursor.fetchone()[0] > 0:
                    # Mappning finns redan - skippa
                    return

                # Skapa mappning enligt schema från guiden
                cursor.execute("""
                    INSERT INTO sub_match_player_mappings (
                        sub_match_id,
                        original_player_id,
                        correct_player_id,
                        correct_player_name,
                        confidence,
                        mapping_reason,
                        notes
                    ) VALUES (?, ?, ?, ?, 90, 'First name mapping', ?)
                """, (
                    sub_match_id,
                    source_player_id,
                    target_player_id,
                    target_player_name,
                    f'Auto-mapped first name: "{source_player_name}" -> "{target_player_name}"'
                ))

                conn.commit()

        except Exception as e:
            error_msg = f"Error creating first name mapping: {str(e)}"
            print(f"ERROR: {error_msg}")
            self.import_log["errors"].append(error_msg)

    def create_contextual_first_name_mapping(self, sub_match_id, source_player_id, target_player_id, target_player_name, source_player_name, club_name):
        """Skapa kontextuell första namn mappning enligt etablerat schema"""
        try:
            with sqlite3.connect(self.db.db_path) as conn:
                cursor = conn.cursor()

                # Kolla om mappning redan finns för denna sub-match och spelare
                cursor.execute("""
                    SELECT COUNT(*) FROM sub_match_player_mappings
                    WHERE sub_match_id = ? AND original_player_id = ?
                """, (sub_match_id, source_player_id))

                if cursor.fetchone()[0] > 0:
                    # Mappning finns redan - skippa
                    return

                # Skapa mappning enligt schema från guiden
                cursor.execute("""
                    INSERT INTO sub_match_player_mappings (
                        sub_match_id,
                        original_player_id,
                        correct_player_id,
                        correct_player_name,
                        confidence,
                        mapping_reason,
                        notes
                    ) VALUES (?, ?, ?, ?, 85, 'Contextual first name mapping', ?)
                """, (
                    sub_match_id,
                    source_player_id,
                    target_player_id,
                    target_player_name,
                    f'Auto-created contextual mapping: "{source_player_name}" -> "{target_player_name}" (club: {club_name})'
                ))

                conn.commit()

        except Exception as e:
            error_msg = f"Error creating contextual first name mapping: {str(e)}"
            print(f"ERROR: {error_msg}")
            self.import_log["errors"].append(error_msg)

    def needs_club_context(self, raw_player_name: str, mapping_result: dict) -> bool:
        """Avgör om vi behöver klubb-kontext för nya spelare"""

        # VIKTIGT: Om SmartPlayerMatcher returnerade låg confidence MEN hittade en match,
        # betyder det att spelaren troligen finns men kräver mappning/separation
        action = mapping_result.get('action', '')
        confidence = mapping_result.get('confidence', 0)

        # Om matcher hittades men confidence är låg = namn-konflikt
        if mapping_result.get('player_id') and confidence < 75:
            return True

        if 'multiple' in action.lower() or 'conflict' in action.lower():
            return True

        # Kontrollera om exakt namnet redan finns i databasen
        try:
            with sqlite3.connect(self.db.db_path) as conn:
                cursor = conn.cursor()

                # Kolla direkt namn-match
                cursor.execute("SELECT COUNT(*) FROM players WHERE name = ?", (raw_player_name,))
                exact_count = cursor.fetchone()[0]

                if exact_count > 0:
                    return True

                # Kolla också om det finns case variations eller mappningar
                cursor.execute("SELECT COUNT(*) FROM players WHERE LOWER(name) = LOWER(?)", (raw_player_name,))
                case_count = cursor.fetchone()[0]

                if case_count > 0:
                    return True

                # Kolla befintliga mappningar
                cursor.execute("""
                    SELECT COUNT(*)
                    FROM sub_match_player_mappings smpm
                    JOIN players p ON smpm.original_player_id = p.id
                    WHERE LOWER(p.name) = LOWER(?)
                """, (raw_player_name,))
                mapping_count = cursor.fetchone()[0]

                if mapping_count > 0:
                    return True

        except Exception:
            # Vid fel, var säker och använd klubb-kontext
            return True

        # Helt nytt namn - ingen klubb-kontext behövs
        return False

    def generate_contextual_player_name(self, raw_name: str, team_name: str) -> str:
        """GENERELL kontextuell namngivning för nya spelare"""
        import re

        # Extrahera klubbnamn (ta bort divisions-info)
        club_name = re.sub(r'\\s*\\([^)]*\\)$', '', team_name).strip()

        # Skapa kontextuellt namn: "Spelarnamn (Klubb)"
        return f"{raw_name} ({club_name})"

    def get_team_name_by_id(self, team_id: int) -> str:
        """Hämta teamnamn från database"""
        try:
            with sqlite3.connect(self.db.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM teams WHERE id = ?", (team_id,))
                result = cursor.fetchone()
                return result[0] if result else f"Team_{team_id}"
        except:
            return f"Team_{team_id}"

    def log_player_action(self, action_type: str, player_name: str, details: dict):
        """Detaljerad loggning av alla spelarbeslut"""
        log_entry = {
            "timestamp": datetime.datetime.now().isoformat(),
            "action": action_type,
            "raw_player_name": player_name,
            "details": details
        }

        self.import_log["players_handled"].append(log_entry)

        # Realtids konsoll-output
        if action_type == "AUTO_ACCEPT_HIGH_CONFIDENCE":
            print(f"    + {player_name} -> {details.get('player_name', 'N/A')} ({details.get('confidence', 0)}%)")
        elif action_type == "AUTO_ACCEPT_MEDIUM_CONFIDENCE":
            print(f"    ? {player_name} -> {details.get('player_name', 'N/A')} ({details.get('confidence', 0)}%)")
        elif action_type == "AUTO_CREATE_WITH_CONTEXT":
            print(f"    # Skapade med kontext: {details.get('created_name', 'N/A')}")
        elif action_type == "AUTO_CREATE_NEW":
            print(f"    * Ny spelare: {details.get('created_name', 'N/A')}")
        elif action_type == "AUTO_CASE_VARIATION_MAPPED":
            print(f"    ~ Case-mappning: {player_name} -> {details.get('player_name', 'N/A')} ({details.get('confidence', 0)}%)")
        elif action_type == "AUTO_FIRST_NAME_MAPPED":
            print(f"    @ Förnamn-mappning: {player_name} -> {details.get('player_name', 'N/A')} ({details.get('confidence', 0)}%)")
        elif action_type == "AUTO_CREATE_CONTEXTUAL_MAPPING":
            print(f"    & Kontextuell mappning: {details.get('source_name', 'N/A')} -> {details.get('target_name', 'N/A')} (club: {details.get('club', 'N/A')})")

    def import_sub_match_smart(self, match_data: Dict, team1_id: int, team2_id: int, match_id: int, match_number: int = 1, team1_name: str = None, team2_name: str = None):
        """Import sub-match med smart player handling - ersätter original import_sub_match"""
        try:
            submatch_data = match_data

            # Create sub-match record med match_number (samma som NewSeasonImporter)
            game_name = submatch_data.get('gameName', 'Unknown')
            game_mode = submatch_data.get('gameMode', 'Singles')

            # AD (Avgörande Dubbel) should always be Doubles, regardless of gameMode
            if ' AD' in game_name or game_name.endswith('AD'):
                game_mode = 'Doubles'

            sub_match_info = {
                'match_id': match_id,
                'match_number': match_number,
                'match_type': game_mode,
                'match_name': game_name,
                'team1_legs': submatch_data.get('t1SetCnt', 0),
                'team2_legs': submatch_data.get('t2SetCnt', 0)
            }

            sub_match_id = self.db.insert_sub_match(sub_match_info)

            # Import players med SMART MATCHING
            stats_data = submatch_data.get('statsData', [])
            self.import_players_smart(sub_match_id, stats_data, team1_id, team2_id, team1_name, team2_name)

            # Import legs and throws (unchanged)
            leg_data_list = submatch_data.get('legData', [])
            for leg_index, leg_data in enumerate(leg_data_list, 1):
                self.import_leg(sub_match_id, leg_index, leg_data)

            return sub_match_id

        except Exception as e:
            error_msg = f"Error importing sub-match: {e}"
            print(f"ERROR: {error_msg}")
            self.import_log["errors"].append(error_msg)
            raise

    def import_from_url_file_smart(self, url_file_path: str, division_id: str) -> Dict[str, int]:
        """Import från URL-fil med smart spelarmappning"""
        matches_imported = 0

        print(f"Laser {url_file_path}")

        # Läs URL-filen
        with open(url_file_path, 'r', encoding='utf-8') as f:
            urls = [line.strip() for line in f if line.strip() and not line.startswith('#')]

        print(f"  Testar {len(urls)} URLs for spelade matcher...")

        # Process each URL
        for i, url in enumerate(urls):
            try:
                # Fetch match data
                response = self.session.get(url, timeout=10)

                if response.status_code == 200:
                    match_data = response.json()

                    if match_data and len(match_data) > 0:
                        # Använd samma logik som NewSeasonImporter
                        match_info = self.extract_match_info(match_data, "2025/2026")

                        if match_info:
                            success, is_new = self.import_match_with_smart_players(match_info)
                            if success and is_new:
                                matches_imported += 1

                        if matches_imported % 3 == 0 and matches_imported > 0:
                            print(f"    {matches_imported} nya matcher importerade...")

                # Rate limiting
                time.sleep(0.5)

            except Exception as e:
                # Stil failure - fortsätt med nästa URL
                continue

        print(f"  Import slutford: {matches_imported} matcher, {self.import_log['statistics']['total_players_processed']} spelare")

        return {
            "matches_imported": matches_imported,
            "players_processed": self.import_log["statistics"]["total_players_processed"],
            "player_statistics": self.import_log["statistics"],
            "warnings": self.import_log["warnings"],
            "errors": self.import_log["errors"]
        }

    def import_match_with_smart_players(self, match_info: dict) -> tuple:
        """Exakt samma som NewSeasonImporter.import_match() men med smart spelarmappning
        Returns (success: bool, is_new: bool)"""
        try:
            # Get or create teams (samma som NewSeasonImporter)
            team1_id = self.db.get_or_create_team(match_info['team1_name'], match_info['division'])
            team2_id = self.db.get_or_create_team(match_info['team2_name'], match_info['division'])

            # Insert main match (samma som NewSeasonImporter)
            match_data = {
                'match_url': match_info['match_url'],
                'team1_id': team1_id,
                'team2_id': team2_id,
                'team1_score': match_info['team1_score'],
                'team2_score': match_info['team2_score'],
                'team1_avg': match_info['team1_avg'],
                'team2_avg': match_info['team2_avg'],
                'division': match_info['division'],
                'season': match_info['season'],
                'match_date': match_info['match_date']
            }

            match_id, is_new = self.db.insert_match(match_data)

            # Process each sub-match MED SMART SPELARMAPPNING (only if new match)
            if is_new:
                for submatch in match_info['sub_matches']:
                    self.import_submatch_with_smart_players(match_id, submatch, team1_id, team2_id,
                                                          match_info['team1_name'], match_info['team2_name'])

            return (True, is_new)

        except Exception as e:
            error_msg = f"Error importing match: {str(e)}"
            print(f"ERROR: {error_msg}")
            self.import_log["errors"].append(error_msg)
            return (False, False)

    def import_submatch_with_smart_players(self, match_id: int, submatch_data: dict, team1_id: int, team2_id: int, team1_name: str, team2_name: str):
        """Exakt samma som NewSeasonImporter.import_submatch() men med smart spelarmappning"""
        try:
            # Extract sub-match info (samma som NewSeasonImporter)
            title = submatch_data.get('title', '')
            # AD (Avgörande Dubbel) is always Doubles
            if 'Doubles' in title or ' AD' in title or title.endswith('AD'):
                match_type = 'Doubles'
            else:
                match_type = 'Singles'

            # Get match name from title
            match_name = title

            # Get leg wins for each team
            stats = submatch_data.get('statsData', [])
            team1_legs = stats[0].get('winLegs', 0) if len(stats) > 0 else 0
            team2_legs = stats[1].get('winLegs', 0) if len(stats) > 1 else 0

            # Calculate averages for this sub-match
            team1_avg = 0
            team2_avg = 0
            if len(stats) >= 2:
                team1_score = stats[0].get('allScore', 0)
                team1_darts = stats[0].get('allDarts', 0)
                team2_score = stats[1].get('allScore', 0)
                team2_darts = stats[1].get('allDarts', 0)

                team1_avg = round((team1_score / max(1, team1_darts)) * 3, 2) if team1_darts > 0 else 0
                team2_avg = round((team2_score / max(1, team2_darts)) * 3, 2) if team2_darts > 0 else 0

            # Insert sub-match (samma som NewSeasonImporter)
            sub_match_data = {
                'match_id': match_id,
                'match_number': 1,
                'match_type': match_type,
                'match_name': match_name,
                'team1_legs': team1_legs,
                'team2_legs': team2_legs,
                'team1_avg': team1_avg,
                'team2_avg': team2_avg,
                'mid': submatch_data.get('mid', '')
            }

            sub_match_id = self.db.insert_sub_match(sub_match_data)

            # Import players MED SMART MAPPNING
            self.import_players_smart(sub_match_id, stats, team1_id, team2_id, team1_name, team2_name)

            # Import legs and throws (samma som NewSeasonImporter)
            leg_data_list = submatch_data.get('legData', [])
            for leg_index, leg_data in enumerate(leg_data_list, 1):
                self.import_leg(sub_match_id, leg_index, leg_data)

        except Exception as e:
            error_msg = f"Error importing submatch: {str(e)}"
            print(f"ERROR: {error_msg}")
            self.import_log["errors"].append(error_msg)
            raise

    def import_match_smart(self, match_data: dict, division_id: str):
        """Import en match med smart player handling"""
        try:
            # Extract match info - wrap single match in list as expected by extract_match_info
            match_info = self.extract_match_info([match_data], "2025/2026")

            # Get or create teams
            team1_id = self.db.get_or_create_team(match_info['team1_name'], division_id)
            team2_id = self.db.get_or_create_team(match_info['team2_name'], division_id)

            # Create match record
            match_record = {
                'match_date': match_info['match_date'],
                'team1_id': team1_id,
                'team2_id': team2_id,
                'team1_score': match_info['team1_score'],
                'team2_score': match_info['team2_score'],
                'season': match_info['season'],
                'division': division_id,
                'match_url': match_info.get('match_url', '')
            }

            match_id, is_new = self.db.insert_match(match_record)

            # Import sub-matches med smart player handling
            sub_matches = match_data.get('subMatches', [match_data])  # Handle both formats

            for match_number, sub_match_data in enumerate(sub_matches, 1):
                self.import_sub_match_smart(sub_match_data, team1_id, team2_id, match_id, match_number)

        except Exception as e:
            error_msg = f"Error importing match: {str(e)}"
            print(f"ERROR: {error_msg}")
            self.import_log["errors"].append(error_msg)
            raise

    def get_import_statistics(self) -> dict:
        """Hämta import-statistik"""
        return {
            "statistics": self.import_log["statistics"],
            "warnings": self.import_log["warnings"],
            "errors": self.import_log["errors"],
            "players_handled_sample": self.import_log["players_handled"][-10:]  # Last 10 for debugging
        }