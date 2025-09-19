import sqlite3
import os
from typing import Optional, List, Dict, Any

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
    
    def get_or_create_player(self, name: str) -> int:
        """Get player ID or create new player if it doesn't exist"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Try to find existing player
            cursor.execute("SELECT id FROM players WHERE name = ?", (name,))
            result = cursor.fetchone()
            
            if result:
                return result[0]
            
            # Create new player
            cursor.execute("INSERT INTO players (name) VALUES (?)", (name,))
            return cursor.lastrowid
    
    def insert_match(self, match_data: Dict[str, Any]) -> int:
        """Insert a new match and return its ID. Returns existing ID if match already exists."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Check if match already exists based on match_url
            if 'match_url' in match_data and match_data['match_url']:
                cursor.execute("SELECT id FROM matches WHERE match_url = ?", (match_data['match_url'],))
                result = cursor.fetchone()
                if result:
                    return result[0]  # Return existing match ID
            
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
            
            return cursor.lastrowid
    
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
    
    def get_player_stats(self, player_name: str, season: str = None, division: str = None, team_filter: str = None) -> Dict[str, Any]:
        """Get comprehensive stats for a player with optional filtering"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Get player ID
            cursor.execute("SELECT id FROM players WHERE name = ?", (player_name,))
            player_result = cursor.fetchone()
            if not player_result:
                return {}
            
            player_id = player_result['id']
            
            # Build WHERE clause for filtering
            where_conditions = ["smp.player_id = ?"]
            params = [player_id]
            
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
                # Get opponents for this sub-match (only from the opposing team)
                opposing_team = 2 if match['team_number'] == 1 else 1
                cursor.execute("""
                    SELECT p.name 
                    FROM sub_match_participants smp2
                    JOIN players p ON smp2.player_id = p.id
                    WHERE smp2.sub_match_id = ? AND smp2.team_number = ?
                    ORDER BY p.name
                """, (match['sub_match_id'], opposing_team))
                
                opponents = [row[0] for row in cursor.fetchall()]
                
                if match['match_type'] == 'Singles':
                    match['opponent'] = opponents[0] if opponents else 'Unknown'
                else:  # Doubles
                    match['opponent'] = ' + '.join(opponents) if opponents else 'Unknown'
            
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
            singles_avg_score = sum(match['player_avg'] for match in singles_avg_matches) / max(1, len(singles_avg_matches)) if singles_avg_matches else 0
            
            # Doubles stats  
            doubles_total = len(doubles_matches)
            doubles_wins = sum(1 for match in doubles_matches if match['won'])
            doubles_losses = doubles_total - doubles_wins
            
            return {
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