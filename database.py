import sqlite3
import os
from typing import Optional, List, Dict, Any

def get_effective_player_ids_for_database(cursor, player_name):
    """
    Get player ID for the given player name.
    Sub-match mappings are handled in the SQL queries, not here.
    """
    cursor.execute("SELECT id FROM players WHERE name = ?", (player_name,))
    result = cursor.fetchone()
    return [result['id']] if result else []

class DartDatabase:
    def __init__(self, db_path: str = "goldenstat.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize the database with schema if it doesn't exist"""
        if not os.path.exists(self.db_path):
            with sqlite3.connect(self.db_path) as conn:
                # Read and execute schema
                schema_path = os.path.join(os.path.dirname(__file__), "database_schema.sql")
                if os.path.exists(schema_path):
                    with open(schema_path, 'r') as f:
                        conn.executescript(f.read())
                conn.commit()
    
    def get_or_create_team(self, name: str, division: Optional[str] = None) -> int:
        """Get team ID or create new team if it doesn't exist"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Try to find existing team
            cursor.execute("SELECT id FROM teams WHERE name = ?", (name,))
            result = cursor.fetchone()
            
            if result:
                return result[0]
            
            # Create new team
            cursor.execute(
                "INSERT INTO teams (name, division) VALUES (?, ?)",
                (name, division)
            )
            return cursor.lastrowid
    
    def normalize_player_name(self, name: str) -> str:
        """Normalisera spelarnamn för att förhindra case-variation dubletter"""
        if not name:
            return name

        # Lista över klubbförkortningar som INTE ska normaliseras
        club_abbreviations = {
            'AC DC', 'ACDC', 'DK Pilo', 'VH Sportbar', 'HMT Dart', 'AIK Dart',
            'TYO DC', 'SSDC', 'TTVH Dartclub', 'SpikKastarna', 'PK Pilsättarna',
            'Cobra DC', 'Tyresö DC', 'Mitt i DC', 'Stockholm Bullseye',
            'Belkin Power', 'Rockhangers', 'Nacka Wermdo', 'Sweden Capital',
            'Oilers', 'Engelen', 'Bålsta', 'Oasen'
        }

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

                # Normalisera personnamnet (före parenteser)
                normalized_before = ' '.join(word.capitalize() for word in before_paren.split() if word)

                # Kontrollera om parentesinnehållet är en känd klubbförkortning
                normalized_paren = paren_content

                # Kolla om det matchar någon känd klubb (case-insensitive)
                is_known_club = False
                for club in club_abbreviations:
                    if paren_content.lower() == club.lower():
                        normalized_paren = club  # Behåll originalet
                        is_known_club = True
                        break

                if not is_known_club:
                    # Inte en känd klubb - normalisera som vanligt namn
                    normalized_paren = ' '.join(word.capitalize() for word in paren_content.split() if word)

                # Normalisera efter-parenteser (om det finns)
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

    def get_or_create_player(self, name: str) -> int:
        """Get player ID or create new player if it doesn't exist"""
        # Normalisera namnet först för att förhindra case-variation dubletter
        normalized_name = self.normalize_player_name(name)

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Try to find existing player med normalized namn
            cursor.execute("SELECT id FROM players WHERE name = ?", (normalized_name,))
            result = cursor.fetchone()

            if result:
                return result[0]

            # Create new player med normalized namn
            cursor.execute("INSERT INTO players (name) VALUES (?)", (normalized_name,))
            return cursor.lastrowid
    
    def insert_match(self, match_data: Dict[str, Any]) -> tuple:
        """Insert a new match and return (ID, is_new). Returns (existing_ID, False) if match already exists."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Check if match already exists based on match_url
            if 'match_url' in match_data and match_data['match_url']:
                cursor.execute("SELECT id FROM matches WHERE match_url = ?", (match_data['match_url'],))
                result = cursor.fetchone()
                if result:
                    return (result[0], False)  # Return existing match ID and False (not new)

            cursor.execute("""
                INSERT INTO matches
                (match_url, team1_id, team2_id, team1_score, team2_score,
                 team1_avg, team2_avg, division, season, match_date)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                match_data.get('match_url'),
                match_data['team1_id'],
                match_data['team2_id'],
                match_data['team1_score'],
                match_data['team2_score'],
                match_data.get('team1_avg'),
                match_data.get('team2_avg'),
                match_data.get('division'),
                match_data.get('season'),
                match_data.get('match_date')
            ))

            return (cursor.lastrowid, True)  # Return new match ID and True (is new)
    
    def insert_sub_match(self, sub_match_data: Dict[str, Any]) -> int:
        """Insert a sub-match and return its ID. Returns existing ID if sub-match already exists."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Check if sub-match already exists based on unique combination
            # First check by mid (source match ID) if available
            if sub_match_data.get('mid'):
                cursor.execute("""
                    SELECT id FROM sub_matches 
                    WHERE match_id = ? AND mid = ?
                """, (
                    sub_match_data['match_id'],
                    sub_match_data['mid']
                ))
                result = cursor.fetchone()
                if result:
                    return result[0]  # Return existing sub-match ID
            
            # Fallback to old method for matches without mid
            cursor.execute("""
                SELECT id FROM sub_matches 
                WHERE match_id = ? AND match_number = ? AND match_type = ? AND match_name = ?
            """, (
                sub_match_data['match_id'],
                sub_match_data['match_number'],
                sub_match_data['match_type'],
                sub_match_data['match_name']
            ))
            result = cursor.fetchone()
            if result:
                return result[0]  # Return existing sub-match ID
            
            cursor.execute("""
                INSERT INTO sub_matches 
                (match_id, match_number, match_type, match_name, team1_legs, 
                 team2_legs, team1_avg, team2_avg, mid)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                sub_match_data['match_id'],
                sub_match_data['match_number'],
                sub_match_data['match_type'],
                sub_match_data['match_name'],
                sub_match_data['team1_legs'],
                sub_match_data['team2_legs'],
                sub_match_data.get('team1_avg'),
                sub_match_data.get('team2_avg'),
                sub_match_data.get('mid')
            ))
            
            return cursor.lastrowid
    
    def insert_sub_match_participant(self, participant_data: Dict[str, Any]):
        """Insert a sub-match participant. Skips if participant already exists."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Check if participant already exists
            cursor.execute("""
                SELECT id FROM sub_match_participants 
                WHERE sub_match_id = ? AND player_id = ? AND team_number = ?
            """, (
                participant_data['sub_match_id'],
                participant_data['player_id'],
                participant_data['team_number']
            ))
            result = cursor.fetchone()
            if result:
                return  # Participant already exists, skip
            
            cursor.execute("""
                INSERT INTO sub_match_participants 
                (sub_match_id, player_id, team_number, player_avg)
                VALUES (?, ?, ?, ?)
            """, (
                participant_data['sub_match_id'],
                participant_data['player_id'],
                participant_data['team_number'],
                participant_data.get('player_avg')
            ))
    
    def insert_leg(self, leg_data: Dict[str, Any]) -> int:
        """Insert a leg and return its ID"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO legs 
                (sub_match_id, leg_number, winner_team, first_player_team, total_rounds)
                VALUES (?, ?, ?, ?, ?)
            """, (
                leg_data['sub_match_id'],
                leg_data['leg_number'],
                leg_data['winner_team'],
                leg_data['first_player_team'],
                leg_data['total_rounds']
            ))
            
            return cursor.lastrowid
    
    def insert_throw(self, throw_data: Dict[str, Any]):
        """Insert a throw"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO throws
                (leg_id, team_number, round_number, score, remaining_score, darts_used)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                throw_data['leg_id'],
                throw_data['team_number'],
                throw_data['round_number'],
                throw_data['score'],
                throw_data['remaining_score'],
                throw_data.get('darts_used')
            ))

    def _calculate_weighted_average(self, matches: List[Dict]) -> float:
        """Calculate weighted average for matches, weighting by number of darts used.

        This is the CORRECT way to calculate overall average - not simply averaging the averages.
        """
        if not matches:
            return 0.0

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            total_score = 0.0
            total_darts = 0

            for match in matches:
                sub_match_id = match.get('sub_match_id')
                player_avg = match.get('player_avg')
                team_number = match.get('team_number')

                if not sub_match_id or not player_avg or not team_number:
                    continue

                # Count darts for this match (using correct checkout logic)
                cursor.execute('''
                    SELECT l.leg_number, t.score, t.darts_used, t.remaining_score
                    FROM legs l
                    JOIN throws t ON t.leg_id = l.id
                    WHERE l.sub_match_id = ? AND t.team_number = ?
                    ORDER BY l.leg_number, t.id
                ''', (sub_match_id, team_number))

                all_throws = cursor.fetchall()
                match_darts = 0
                last_remaining = {}

                for leg_num, score, darts_used, remaining in all_throws:
                    # Skip starting throw (score=0, remaining=501)
                    if score == 0 and remaining == 501:
                        continue

                    if remaining == 0:
                        # Checkout - detect format based on score value
                        if score <= 3:
                            # Standard format: score = number of darts
                            checkout_darts = score if score else 3
                        else:
                            # Alternative format: score = points, use darts_used
                            checkout_darts = darts_used if darts_used else 3
                        match_darts += checkout_darts
                    else:
                        # Regular throw: always count darts (even if score=0 for missed throws)
                        match_darts += (darts_used if darts_used else 3)
                        if score > 0:
                            last_remaining[leg_num] = remaining

                # Calculate score from player_avg and darts
                match_score = (player_avg * match_darts) / 3.0
                total_score += match_score
                total_darts += match_darts

            return (total_score / total_darts * 3.0) if total_darts > 0 else 0.0
    
    def get_effective_player_name(self, player_name: str) -> str:
        """Get the effective (canonical) name for a player - simplified for clean database"""
        # In clean database without mappings, just return the original name
        return player_name
    
    def get_all_player_ids_for_canonical_name(self, canonical_name: str) -> List[int]:
        """Get all player IDs that map to the same canonical name - simplified for clean database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # In clean database, just get the single player ID
            cursor.execute("""
                SELECT id
                FROM players 
                WHERE name = ?
            """, (canonical_name,))
            
            result = cursor.fetchone()
            return [result['id']] if result else []

    def get_player_stats(self, player_name: str, season: str = None, division: str = None, team_filter: str = None) -> Dict[str, Any]:
        """Get comprehensive stats for a player with optional filtering, using mappings"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Get all effective player IDs (including mapped ones)
            all_player_ids = get_effective_player_ids_for_database(cursor, player_name)
            
            if not all_player_ids:
                return {}
            
            # Build WHERE clause that handles sub-match mappings
            player_id = all_player_ids[0]  # Use the first (and should be only) player ID
            where_conditions = [
                """(
                    -- Include direct matches for this player, but exclude mapped-away sub-matches
                    (smp.player_id = ? AND p.name = ? 
                     AND smp.sub_match_id NOT IN (
                         SELECT smpm.sub_match_id 
                         FROM sub_match_player_mappings smpm 
                         WHERE smpm.original_player_id = ?
                     )
                    ) 
                    OR 
                    -- Include sub-matches that are mapped TO this player
                    (smp.sub_match_id IN (
                        SELECT smpm.sub_match_id 
                        FROM sub_match_player_mappings smpm 
                        WHERE smpm.correct_player_name = ?
                    ) AND smp.player_id IN (
                        SELECT DISTINCT smpm2.original_player_id 
                        FROM sub_match_player_mappings smpm2 
                        WHERE smpm2.correct_player_name = ?
                    ))
                )"""
            ]
            params = [player_id, player_name, player_id, player_name, player_name]
            
            if season:
                where_conditions.append("m.season = ?")
                params.append(season)
            
            if division:
                where_conditions.append("m.division = ?")
                params.append(division)
            
            if team_filter:
                where_conditions.append("(CASE WHEN smp.team_number = 1 THEN t1.name ELSE t2.name END) = ?")
                params.append(team_filter)
            
            where_clause = " AND ".join(where_conditions)
            
            # Get all matches for this player with detailed stats and filtering
            cursor.execute(f"""
                SELECT 
                    m.match_date,
                    m.season,
                    m.division,
                    t1.name as team1_name,
                    t2.name as team2_name,
                    sm.match_type,
                    sm.match_name,
                    sm.team1_legs,
                    sm.team2_legs,
                    smp.team_number,
                    smp.player_avg,
                    CASE WHEN smp.team_number = 1 THEN t1.name ELSE t2.name END as player_team,
                    CASE WHEN smp.team_number = 1 THEN t2.name ELSE t1.name END as opponent_team,
                    CASE 
                        WHEN (smp.team_number = 1 AND sm.team1_legs > sm.team2_legs) 
                          OR (smp.team_number = 2 AND sm.team2_legs > sm.team1_legs) 
                        THEN 1 ELSE 0 
                    END as won,
                    sm.id as sub_match_id
                FROM sub_match_participants smp
                JOIN players p ON smp.player_id = p.id
                JOIN sub_matches sm ON smp.sub_match_id = sm.id
                JOIN matches m ON sm.match_id = m.id
                JOIN teams t1 ON m.team1_id = t1.id
                JOIN teams t2 ON m.team2_id = t2.id
                WHERE {where_clause}
                ORDER BY m.match_date DESC
            """, params)
            
            matches = [dict(row) for row in cursor.fetchall()]
            
            # Add opponent information for each match
            for match in matches:
                # Get opponents for this sub-match (only from the opposing team) with correct mapped names
                opposing_team = 2 if match['team_number'] == 1 else 1
                cursor.execute("""
                    SELECT p.name as original_name, smp2.player_id
                    FROM sub_match_participants smp2
                    JOIN players p ON smp2.player_id = p.id
                    WHERE smp2.sub_match_id = ? AND smp2.team_number = ?
                    ORDER BY p.name
                """, (match['sub_match_id'], opposing_team))
                
                opponent_data = cursor.fetchall()
                opponents = []
                
                for opponent in opponent_data:
                    # Check for mapping
                    cursor.execute("""
                        SELECT correct_player_name
                        FROM sub_match_player_mappings
                        WHERE sub_match_id = ? AND original_player_id = ?
                    """, (match['sub_match_id'], opponent['player_id']))
                    
                    mapping_result = cursor.fetchone()
                    display_name = mapping_result['correct_player_name'] if mapping_result else opponent['original_name']
                    opponents.append(display_name)
                
                # Check if this is AD (Avgörande Dubbel) - treat it as Doubles
                is_ad = match['match_name'] and (' AD' in match['match_name'] or match['match_name'].endswith(' AD'))
                is_doubles = match['match_type'] == 'Doubles' or is_ad

                if is_doubles:
                    # Doubles or AD - show both opponents
                    match['opponent'] = ' + '.join(opponents) if opponents else 'Unknown'

                    # Get teammate for doubles matches (from the same team, excluding the current player)
                    cursor.execute("""
                        SELECT p.name as original_name, smp2.player_id
                        FROM sub_match_participants smp2
                        JOIN players p ON smp2.player_id = p.id
                        WHERE smp2.sub_match_id = ? AND smp2.team_number = ? AND smp2.player_id != ?
                        ORDER BY p.name
                    """, (match['sub_match_id'], match['team_number'], player_id))

                    teammate_data = cursor.fetchall()
                    teammates = []

                    for teammate in teammate_data:
                        # Check for mapping
                        cursor.execute("""
                            SELECT correct_player_name
                            FROM sub_match_player_mappings
                            WHERE sub_match_id = ? AND original_player_id = ?
                        """, (match['sub_match_id'], teammate['player_id']))

                        mapping_result = cursor.fetchone()
                        display_name = mapping_result['correct_player_name'] if mapping_result else teammate['original_name']
                        teammates.append(display_name)

                    match['teammate'] = teammates[0] if teammates else None
                else:
                    # Singles - only one opponent, no teammate
                    match['opponent'] = opponents[0] if opponents else 'Unknown'
                    match['teammate'] = None
            
            # Calculate summary stats - separate by match type
            singles_matches = [m for m in matches if m['match_type'] == 'Singles']
            doubles_matches = [m for m in matches if m['match_type'] == 'Doubles']
            
            # Overall stats
            total_matches = len(matches)
            wins = sum(1 for match in matches if match['won'])
            losses = total_matches - wins
            
            # Singles stats
            singles_total = len(singles_matches)
            singles_wins = sum(1 for match in singles_matches if match['won'])
            singles_losses = singles_total - singles_wins
            singles_avg_matches = [m for m in singles_matches if m['player_avg']]

            # Calculate weighted average for singles (weight by number of darts)
            singles_avg_score = self._calculate_weighted_average(singles_avg_matches)
            
            # Doubles stats  
            doubles_total = len(doubles_matches)
            doubles_wins = sum(1 for match in doubles_matches if match['won'])
            doubles_losses = doubles_total - doubles_wins
            
            return {
                'player_id': player_id,
                'player_name': player_name,
                'total_matches': total_matches,
                'wins': wins,
                'losses': losses,
                'win_percentage': (wins / max(1, total_matches)) * 100,
                'average_score': round(singles_avg_score, 2),  # Only from singles as before
                'singles': {
                    'total_matches': singles_total,
                    'wins': singles_wins,
                    'losses': singles_losses,
                    'win_percentage': (singles_wins / max(1, singles_total)) * 100,
                    'average_score': round(singles_avg_score, 2)
                },
                'doubles': {
                    'total_matches': doubles_total,
                    'wins': doubles_wins,
                    'losses': doubles_losses,
                    'win_percentage': (doubles_wins / max(1, doubles_total)) * 100
                },
                'recent_matches': matches  # All matches
            }