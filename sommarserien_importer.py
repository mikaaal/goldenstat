# -*- coding: utf-8 -*-
"""
Importer för StDF & OBDT Sommarserie.

Sommarserien har ett annat matchformat än övriga serier:
  Match 1:   Lag    – 4 spelare/lag, 3x601 SIDO
  Match 2-3: Dubbel – 2 spelare/lag, 3x501 SIDO
  Match 4-7: Singel – 1 spelare/lag, 5x301 DIDO

API-svaret är en platt lista med 7 sub-match-objekt (ingen wrapper-struktur).
Kastnivådata finns fullt ut i playerData [{score, left}] per lag och leg.
Checkout kodas som negativt score (t.ex. -3 = 3 pilar för att avsluta).
"""

from smart_season_importer import SmartSeasonImporter


def _detect_match_type(title: str) -> str:
    """Returnerar 'Team', 'Doubles' eller 'Singles' baserat på sub-matchens titel."""
    lower = title.lower()
    if 'lag' in lower:
        return 'Team'
    if 'dubbel' in lower or 'doubles' in lower or ' ad' in lower or lower.endswith('ad'):
        return 'Doubles'
    return 'Singles'


class SommarserienImporter(SmartSeasonImporter):
    """
    Importer för Sommarserien. Ärver smart spelarmatchning från SmartSeasonImporter
    och hanterar sommarseriens unika sub-matchformat (601/501/301).

    Spelarnamn används exakt som de är registrerade i nakka — ingen kontextuell
    disambiguering med lägnamn, eftersom spelare i sommarserien ofta bara registrerar
    förnamn eller smeknamn.
    """

    def import_players_smart(self, sub_match_id, stats_data, team1_id, team2_id,
                             team1_name=None, team2_name=None):
        """Enklare spelarimport utan kontextuell namnkollision — använd exakt det registrerade namnet."""
        try:
            if not team1_name:
                team1_name = self.get_team_name_by_id(team1_id)
            if not team2_name:
                team2_name = self.get_team_name_by_id(team2_id)

            for team_index, team_stats in enumerate(stats_data):
                team_number = team_index + 1

                all_score = team_stats.get('allScore', 0)
                all_darts = team_stats.get('allDarts', 0)
                player_avg = round((all_score / all_darts) * 3, 2) if all_darts > 0 else 0

                order = team_stats.get('order', [])
                if not order:
                    continue

                for player_info in order:
                    raw_name = player_info.get('oname', 'Unknown').strip()
                    if not raw_name or raw_name == 'Unknown':
                        continue

                    player_name = self.normalize_player_name(raw_name)
                    player_id = self.db.get_or_create_player(player_name)

                    self.db.insert_sub_match_participant({
                        'sub_match_id': sub_match_id,
                        'player_id': player_id,
                        'team_number': team_number,
                        'player_avg': player_avg
                    })
                    self.import_log["statistics"]["total_players_processed"] += 1

        except Exception as e:
            error_msg = f"Error importing players for sub_match {sub_match_id}: {str(e)}"
            print(f"ERROR: {error_msg}")
            self.import_log["errors"].append(error_msg)

    def import_submatch_with_smart_players(
        self,
        match_id: int,
        submatch_data: dict,
        team1_id: int,
        team2_id: int,
        team1_name: str,
        team2_name: str,
    ):
        try:
            title = submatch_data.get('title', '')
            match_type = _detect_match_type(title)

            stats = submatch_data.get('statsData', [])
            team1_legs = stats[0].get('winLegs', 0) if len(stats) > 0 else 0
            team2_legs = stats[1].get('winLegs', 0) if len(stats) > 1 else 0

            team1_avg = team2_avg = 0
            if len(stats) >= 2:
                s1_score = stats[0].get('allScore', 0)
                s1_darts = stats[0].get('allDarts', 0)
                s2_score = stats[1].get('allScore', 0)
                s2_darts = stats[1].get('allDarts', 0)
                team1_avg = round((s1_score / s1_darts) * 3, 2) if s1_darts > 0 else 0
                team2_avg = round((s2_score / s2_darts) * 3, 2) if s2_darts > 0 else 0

            sub_match_data = {
                'match_id': match_id,
                'match_number': 1,
                'match_type': match_type,
                'match_name': title,
                'team1_legs': team1_legs,
                'team2_legs': team2_legs,
                'team1_avg': team1_avg,
                'team2_avg': team2_avg,
                'mid': submatch_data.get('mid', ''),
            }

            sub_match_id = self.db.insert_sub_match(sub_match_data)

            self.import_players_smart(
                sub_match_id, stats, team1_id, team2_id, team1_name, team2_name
            )

            # Importera legs med full kastnivådata
            for leg_index, leg_data in enumerate(submatch_data.get('legData', []), 1):
                self.import_leg(sub_match_id, leg_index, leg_data)

        except Exception as e:
            error_msg = f"Error importing sommarserien submatch: {e}"
            print(f"ERROR: {error_msg}")
            self.import_log["errors"].append(error_msg)
            raise
