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
        """Insert a new match and return its ID"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO matches 
                (match_url, team1_id, team2_id, team1_score, team2_score, 
                 team1_avg, team2_avg, division, season, match_date)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                match_data['match_url'],
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
        """Insert a sub-match and return its ID"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
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
        """Insert a sub-match participant"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
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
    
    def get_player_stats(self, player_name: str) -> Dict[str, Any]:
        """Get comprehensive stats for a player"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Get player ID
            cursor.execute("SELECT id FROM players WHERE name = ?", (player_name,))
            player_result = cursor.fetchone()
            if not player_result:
                return {}
            
            player_id = player_result['id']
            
            # Get all matches for this player with detailed stats
            cursor.execute("""
                SELECT 
                    m.match_date,
                    t1.name as team1_name,
                    t2.name as team2_name,
                    sm.match_type,
                    sm.match_name,
                    sm.team1_legs,
                    sm.team2_legs,
                    smp.team_number,
                    smp.player_avg,
                    CASE WHEN smp.team_number = 1 THEN t1.name ELSE t2.name END as player_team,
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
                WHERE smp.player_id = ?
                ORDER BY m.match_date DESC
            """, (player_id,))
            
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
            
            # Calculate summary stats
            total_matches = len(matches)
            wins = sum(1 for match in matches if match['won'])
            losses = total_matches - wins
            
            # Calculate average only from Singles matches
            singles_matches = [m for m in matches if m['match_type'] == 'Singles' and m['player_avg']]
            avg_score = sum(match['player_avg'] for match in singles_matches) / max(1, len(singles_matches)) if singles_matches else 0
            
            return {
                'player_name': player_name,
                'total_matches': total_matches,
                'wins': wins,
                'losses': losses,
                'win_percentage': (wins / max(1, total_matches)) * 100,
                'average_score': round(avg_score, 2),
                'recent_matches': matches  # All matches
            }