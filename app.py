#!/usr/bin/env python3
"""
GoldenStat Web Application
A Flask web app for viewing dart player statistics
"""

from flask import Flask, render_template, request, jsonify
import json
from datetime import datetime
from database import DartDatabase

app = Flask(__name__)
app.secret_key = 'goldenstat-secret-key'


db = DartDatabase()

@app.route('/')
def index():
    """Main page with player search"""
    return render_template('index.html')


@app.route('/api/teams')
def get_teams():
    """API endpoint to get all team names for autocomplete"""
    try:
        import sqlite3
        with sqlite3.connect(db.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Get all team names that have played matches
            cursor.execute("""
                SELECT DISTINCT t.name 
                FROM teams t 
                JOIN matches m ON (t.id = m.team1_id OR t.id = m.team2_id)
                ORDER BY t.name
            """)
            
            teams = [row['name'] for row in cursor.fetchall()]
            return jsonify(teams)
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/players')
def get_players():
    """API endpoint to get all player names for autocomplete with team disambiguation"""
    try:
        import sqlite3
        with sqlite3.connect(db.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Get players grouped by name and team - treat different teams as different players
            cursor.execute("""
                WITH player_team_stats AS (
                    SELECT 
                        p.id,
                        p.name,
                        CASE WHEN smp.team_number = 1 THEN t1.name ELSE t2.name END as team_name,
                        COUNT(*) as match_count
                    FROM players p
                    JOIN sub_match_participants smp ON p.id = smp.player_id
                    JOIN sub_matches sm ON smp.sub_match_id = sm.id
                    JOIN matches m ON sm.match_id = m.id
                    JOIN teams t1 ON m.team1_id = t1.id
                    JOIN teams t2 ON m.team2_id = t2.id
                    GROUP BY p.id, p.name, team_name
                    HAVING COUNT(*) >= 3  -- Only show teams with 3+ matches to filter noise
                ),
                name_team_counts AS (
                    SELECT name, COUNT(DISTINCT team_name) as team_count
                    FROM player_team_stats
                    GROUP BY name
                )
                SELECT 
                    pts.name,
                    pts.team_name,
                    pts.match_count,
                    ntc.team_count,
                    CASE 
                        WHEN ntc.team_count > 1 THEN pts.name || ' (' || pts.team_name || ')'
                        ELSE pts.name 
                    END as display_name
                FROM player_team_stats pts
                JOIN name_team_counts ntc ON pts.name = ntc.name
                ORDER BY pts.name, pts.team_name
            """)
            
            players = []
            
            for row in cursor.fetchall():
                players.append(row['display_name'])
                    
            return jsonify(players)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/player/<player_name>')
def get_player_stats(player_name):
    """API endpoint to get detailed player statistics"""
    try:
        # Get parameters
        limit = request.args.get('limit', type=int)
        season = request.args.get('season')
        division = request.args.get('division')
        
        # Check if player name includes team disambiguation like "Name (Team)"
        team_filter = None
        if '(' in player_name and player_name.endswith(')'):
            # Extract team from player name like "Mats Andersson (SpikKastarna (SL6))"
            base_name = player_name.split(' (')[0]
            team_part = player_name.split(' (', 1)[1][:-1]  # Remove last )
            team_filter = team_part
            player_name = base_name
        
        stats = db.get_player_stats(player_name, season=season, division=division, team_filter=team_filter)
        if not stats:
            return jsonify({'error': 'Player not found'}), 404
        
        # Apply limit if specified
        if limit and 'recent_matches' in stats:
            stats['recent_matches'] = stats['recent_matches'][:limit]
        
        # Convert datetime objects to strings for JSON serialization
        if 'recent_matches' in stats:
            for match in stats['recent_matches']:
                if 'match_date' in match and match['match_date']:
                    match['match_date'] = str(match['match_date'])
        
        # Add filter information to response
        stats['filters'] = {
            'season': season,
            'division': division,
            'team': team_filter
        }
        
        return jsonify(stats)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/player/<player_name>/detailed')
def get_player_detailed_stats(player_name):
    """Get detailed player statistics including match history and trends"""
    try:
        import sqlite3
        with sqlite3.connect(db.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Get player ID
            cursor.execute("SELECT id FROM players WHERE name = ?", (player_name,))
            player_result = cursor.fetchone()
            if not player_result:
                return jsonify({'error': 'Player not found'}), 404
            
            player_id = player_result['id']
            
            # Get detailed match history with averages over time
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
                ORDER BY m.match_date DESC, sm.match_number
            """, (player_id,))
            
            matches = [dict(row) for row in cursor.fetchall()]
            
            # Get match type breakdown
            cursor.execute("""
                SELECT 
                    sm.match_type,
                    COUNT(*) as total_matches,
                    SUM(CASE 
                        WHEN (smp.team_number = 1 AND sm.team1_legs > sm.team2_legs) 
                          OR (smp.team_number = 2 AND sm.team2_legs > sm.team1_legs) 
                        THEN 1 ELSE 0 
                    END) as wins,
                    AVG(smp.player_avg) as avg_score
                FROM sub_match_participants smp
                JOIN sub_matches sm ON smp.sub_match_id = sm.id
                WHERE smp.player_id = ?
                GROUP BY sm.match_type
            """, (player_id,))
            
            match_type_stats = [dict(row) for row in cursor.fetchall()]
            
            # Calculate trends (last 10 vs previous 10)
            recent_matches = matches[:10] if len(matches) >= 10 else matches
            previous_matches = matches[10:20] if len(matches) >= 20 else []
            
            recent_avg = sum(m['player_avg'] for m in recent_matches if m['player_avg']) / max(1, len([m for m in recent_matches if m['player_avg']]))
            previous_avg = sum(m['player_avg'] for m in previous_matches if m['player_avg']) / max(1, len([m for m in previous_matches if m['player_avg']])) if previous_matches else recent_avg
            
            # Convert dates for JSON
            for match in matches:
                if match['match_date']:
                    match['match_date'] = str(match['match_date'])
            
            return jsonify({
                'player_name': player_name,
                'match_history': matches,
                'match_type_breakdown': match_type_stats,
                'trends': {
                    'recent_average': round(recent_avg, 2),
                    'previous_average': round(previous_avg, 2),
                    'improvement': round(recent_avg - previous_avg, 2)
                }
            })
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/player/<player_name>')
def player_detail(player_name):
    """Player detail page"""
    return render_template('player_detail.html', player_name=player_name)

@app.route('/sub_match_throws')
def sub_match_throws():
    """Sub-match throws visualization page"""
    return render_template('sub_match_throws.html')

@app.route('/test_throws')
def test_throws():
    """Test page for throws visualization"""
    return render_template('test_throws.html')

@app.route('/api/leagues')
def get_leagues():
    """Get available leagues and seasons"""
    try:
        import sqlite3
        with sqlite3.connect(db.db_path) as conn:
            cursor = conn.cursor()
            
            # Get distinct seasons and divisions
            cursor.execute("""
                SELECT DISTINCT season, division 
                FROM matches 
                WHERE season IS NOT NULL OR division IS NOT NULL
                ORDER BY season DESC, division ASC
            """)
            
            leagues = []
            seasons = set()
            divisions = set()
            
            for row in cursor.fetchall():
                season = row[0] or 'Unknown'
                division = row[1] or 'Unknown'
                leagues.append({'season': season, 'division': division})
                seasons.add(season)
                divisions.add(division)
            
            return jsonify({
                'leagues': leagues,
                'seasons': sorted(list(seasons), reverse=True),
                'divisions': sorted(list(divisions))
            })
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/overview')
def get_overview():
    """Get database overview statistics"""
    try:
        import sqlite3
        with sqlite3.connect(db.db_path) as conn:
            cursor = conn.cursor()
            
            # Get query parameters for filtering
            season = request.args.get('season')
            division = request.args.get('division')
            
            # Build WHERE clause for filtering
            where_conditions = []
            params = []
            
            if season:
                where_conditions.append("m.season = ?")
                params.append(season)
            
            if division:
                where_conditions.append("m.division = ?")
                params.append(division)
            
            where_clause = " AND ".join(where_conditions)
            if where_clause:
                where_clause = " WHERE " + where_clause
            
            # Get basic counts with filtering
            cursor.execute(f"SELECT COUNT(DISTINCT p.id) FROM players p JOIN sub_match_participants smp ON p.id = smp.player_id JOIN sub_matches sm ON smp.sub_match_id = sm.id JOIN matches m ON sm.match_id = m.id{where_clause}", params)
            total_players = cursor.fetchone()[0]
            
            cursor.execute(f"SELECT COUNT(*) FROM matches m{where_clause}", params)
            total_matches = cursor.fetchone()[0]
            
            cursor.execute(f"SELECT COUNT(*) FROM sub_matches sm JOIN matches m ON sm.match_id = m.id{where_clause}", params)
            total_sub_matches = cursor.fetchone()[0]
            
            cursor.execute(f"SELECT COUNT(*) FROM legs l JOIN sub_matches sm ON l.sub_match_id = sm.id JOIN matches m ON sm.match_id = m.id{where_clause}", params)
            total_legs = cursor.fetchone()[0]
            
            cursor.execute(f"SELECT COUNT(*) FROM throws t JOIN legs l ON t.leg_id = l.id JOIN sub_matches sm ON l.sub_match_id = sm.id JOIN matches m ON sm.match_id = m.id{where_clause}", params)
            total_throws = cursor.fetchone()[0]
            
            # Get recent activity with filtering
            cursor.execute(f"""
                SELECT 
                    t1.name as team1, t2.name as team2,
                    m.team1_score, m.team2_score,
                    m.scraped_at, m.season, m.division
                FROM matches m
                JOIN teams t1 ON m.team1_id = t1.id  
                JOIN teams t2 ON m.team2_id = t2.id
                {where_clause}
                ORDER BY m.scraped_at DESC
                LIMIT 5
            """, params)
            
            recent_matches = []
            for row in cursor.fetchall():
                recent_matches.append({
                    'team1': row[0],
                    'team2': row[1], 
                    'team1_score': row[2],
                    'team2_score': row[3],
                    'scraped_at': str(row[4]),
                    'season': row[5],
                    'division': row[6]
                })
            
            return jsonify({
                'total_players': total_players,
                'total_matches': total_matches,
                'total_sub_matches': total_sub_matches,
                'total_legs': total_legs,
                'total_throws': total_throws,
                'recent_matches': recent_matches,
                'filters': {
                    'season': season,
                    'division': division
                }
            })
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/player/<player_name>/throws')
def get_player_throws(player_name):
    """Get detailed throw analysis for a player"""
    try:
        import sqlite3
        with sqlite3.connect(db.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Get filter parameters
            season = request.args.get('season')
            division = request.args.get('division')
            
            # Check if player name includes team disambiguation like "Name (Team)"
            team_filter = None
            original_player_name = player_name
            if '(' in player_name and player_name.endswith(')'):
                # Extract team from player name like "Mats Andersson (SpikKastarna (SL6))"
                base_name = player_name.split(' (')[0]
                team_part = player_name.split(' (', 1)[1][:-1]  # Remove last )
                team_filter = team_part
                player_name = base_name
                print(f"DEBUG: Original: '{original_player_name}' -> Base: '{player_name}', Team: '{team_filter}'", flush=True)
            
            # Get player ID
            cursor.execute("SELECT id FROM players WHERE name = ?", (player_name,))
            player_result = cursor.fetchone()
            if not player_result:
                return jsonify({'error': 'Player not found'}), 404
            
            player_id = player_result['id']
            
            # Build WHERE clause for filtering
            where_conditions = ["smp.player_id = ? AND t.team_number = smp.team_number AND sm.match_type = 'Singles'"]
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
            
            # Get detailed throw data - ONLY from Singles matches with filtering
            cursor.execute(f"""
                SELECT 
                    t.score,
                    t.remaining_score,
                    t.darts_used,
                    t.round_number,
                    l.leg_number,
                    sm.match_type,
                    sm.match_name,
                    m.match_date,
                    smp.player_avg,
                    CASE 
                        WHEN (smp.team_number = 1 AND sm.team1_legs > sm.team2_legs) 
                          OR (smp.team_number = 2 AND sm.team2_legs > sm.team1_legs) 
                        THEN 1 ELSE 0 
                    END as won_match
                FROM throws t
                JOIN legs l ON t.leg_id = l.id
                JOIN sub_matches sm ON l.sub_match_id = sm.id
                JOIN sub_match_participants smp ON sm.id = smp.sub_match_id
                JOIN matches m ON sm.match_id = m.id
                JOIN teams t1 ON m.team1_id = t1.id
                JOIN teams t2 ON m.team2_id = t2.id
                WHERE {where_clause}
                ORDER BY m.match_date DESC, l.leg_number, t.round_number
            """, params)
            
            throws = [dict(row) for row in cursor.fetchall()]
            
            # Calculate throw statistics
            if throws:
                scores = [t['score'] for t in throws if t['score'] > 0]  # For max and ranges
                
                # Use player_avg from database to match main stats exactly
                # Get unique matches and their player_avg values
                unique_matches = {}
                for throw in throws:
                    match_key = f"{throw['match_date']}_{throw['match_name']}"
                    if match_key not in unique_matches and throw['player_avg'] is not None:
                        unique_matches[match_key] = throw['player_avg']
                
                # Calculate average of player_avg values (same as main stats)
                match_averages = list(unique_matches.values())
                avg_score = sum(match_averages) / len(match_averages) if match_averages else 0
                max_score = max(scores) if scores else 0
                
                # Count different score ranges
                score_ranges = {
                    '0-20': len([s for s in scores if 0 <= s <= 20]),
                    '21-40': len([s for s in scores if 21 <= s <= 40]),
                    '41-60': len([s for s in scores if 41 <= s <= 60]),
                    '61-80': len([s for s in scores if 61 <= s <= 80]),
                    '81-99': len([s for s in scores if 81 <= s <= 99]),
                    '100+': len([s for s in scores if s >= 100])
                }
                
                # Calculate checkouts (scores when remaining_score became 0)
                checkouts = [t['score'] for t in throws if t['remaining_score'] == 0 and t['score'] > 0]
                
                # Advanced statistics
                throws_over_100 = len([s for s in scores if s >= 100])
                throws_180 = len([s for s in scores if s == 180])
                throws_over_140 = len([s for s in scores if s >= 140])
                throws_26 = len([s for s in scores if s == 26])
                throws_under_20 = len([s for s in scores if s < 20])
                
                # High finishes (checkouts 100+)
                high_finishes = len([t['score'] for t in throws if t['remaining_score'] == 0 and t['score'] >= 100])
                
                # Short sets (legs won in 18 darts or fewer)
                # Count legs where player won and used <= 18 darts
                from collections import defaultdict
                leg_darts = defaultdict(int)
                leg_winners = {}
                
                for throw in throws:
                    leg_id = f"{throw['match_date']}_{throw['match_name']}_{throw['leg_number']}"
                    leg_darts[leg_id] += throw['darts_used'] or 3
                    
                    # If this is a finishing throw (remaining_score becomes 0), mark as won
                    if throw['remaining_score'] == 0:
                        leg_winners[leg_id] = True
                
                # Count legs won in 18 darts or fewer
                short_sets = sum(1 for leg_id in leg_winners.keys() if leg_darts[leg_id] <= 18)
                
                # Most common scores
                from collections import Counter
                score_frequency = Counter(scores)
                most_common_scores = score_frequency.most_common(5)
                
                statistics = {
                    'total_throws': len(throws),
                    'average_score': round(avg_score, 2),
                    'max_score': max_score,
                    'score_ranges': score_ranges,
                    'total_checkouts': len(checkouts),
                    'checkout_scores': checkouts,
                    'throws_over_100': throws_over_100,
                    'throws_180': throws_180,
                    'throws_over_140': throws_over_140,
                    'throws_26': throws_26,
                    'throws_under_20': throws_under_20,
                    'high_finishes': high_finishes,
                    'short_sets': short_sets,
                    'most_common_scores': [{'score': score, 'count': count} for score, count in most_common_scores]
                }
                print(f"DEBUG: Total throws for '{original_player_name}': {len(throws)}, Team filter: {team_filter}", flush=True)
            else:
                statistics = {}
            
            # Convert dates for JSON
            for throw in throws:
                if throw['match_date']:
                    throw['match_date'] = str(throw['match_date'])
            
            return jsonify({
                'player_name': player_name,
                'throws': throws[:100],  # Limit to last 100 throws for performance
                'statistics': statistics
            })
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/sub_match/<int:sub_match_id>/throws/<player_name>')
def get_sub_match_player_throws(sub_match_id, player_name):
    """Get detailed throw data for a specific player in a specific sub-match"""
    try:
        import sqlite3
        with sqlite3.connect(db.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Get sub-match info and find the specific player who participated
            # This handles the case where multiple players have the same name
            cursor.execute("""
                SELECT 
                    sm.*,
                    smp.team_number,
                    smp.player_avg,
                    smp.player_id,
                    m.match_date,
                    t1.name as team1_name,
                    t2.name as team2_name
                FROM sub_matches sm
                JOIN sub_match_participants smp ON sm.id = smp.sub_match_id
                JOIN players p ON smp.player_id = p.id
                JOIN matches m ON sm.match_id = m.id
                JOIN teams t1 ON m.team1_id = t1.id
                JOIN teams t2 ON m.team2_id = t2.id
                WHERE sm.id = ? AND p.name = ?
            """, (sub_match_id, player_name))
            
            sub_match_info = cursor.fetchone()
            if not sub_match_info:
                return jsonify({'error': 'Player did not participate in this sub-match'}), 404
                
            player_id = sub_match_info['player_id']
            
            # Get opponent info and averages
            opposing_team_number = 2 if sub_match_info['team_number'] == 1 else 1
            cursor.execute("""
                SELECT p.name, smp.player_avg 
                FROM sub_match_participants smp
                JOIN players p ON smp.player_id = p.id
                WHERE smp.sub_match_id = ? AND smp.team_number = ?
                ORDER BY p.name
            """, (sub_match_id, opposing_team_number))
            
            opponent_data = cursor.fetchall()
            opponents = [row[0] for row in opponent_data]
            opponent_names = ' / '.join(opponents) if len(opponents) > 1 else (opponents[0] if opponents else 'Okänd')
            opponent_avg = sum(row[1] or 0 for row in opponent_data) / len(opponent_data) if opponent_data else 0
            
            # Get teammate info (other players on the same team)
            cursor.execute("""
                SELECT p.name, smp.player_avg 
                FROM sub_match_participants smp
                JOIN players p ON smp.player_id = p.id
                WHERE smp.sub_match_id = ? AND smp.team_number = ? AND smp.player_id != ?
                ORDER BY p.name
            """, (sub_match_id, sub_match_info['team_number'], player_id))
            
            teammate_data = cursor.fetchall()
            teammates = [row[0] for row in teammate_data]
            teammate_names = ' / '.join(teammates) if teammates else None

            # Get all throws for both players in this sub-match
            # Filter out starting throw (score=0, remaining_score=501)
            cursor.execute("""
                SELECT 
                    t.score,
                    t.remaining_score,
                    t.darts_used,
                    t.round_number,
                    t.team_number,
                    l.leg_number,
                    l.winner_team,
                    l.total_rounds as leg_total_rounds
                FROM throws t
                JOIN legs l ON t.leg_id = l.id
                WHERE l.sub_match_id = ?
                  AND NOT (t.score = 0 AND t.remaining_score = 501)
                ORDER BY l.leg_number, t.round_number, t.team_number
            """, (sub_match_id,))
            
            throws = [dict(row) for row in cursor.fetchall()]
            
            # Separate throws by player and opponent
            player_throws = [t for t in throws if t['team_number'] == sub_match_info['team_number']]
            opponent_throws = [t for t in throws if t['team_number'] != sub_match_info['team_number']]
            
            # Group throws by leg with both player and opponent data
            legs_with_throws = {}
            
            for throw in throws:
                leg_num = throw['leg_number']
                if leg_num not in legs_with_throws:
                    # Determine leg winner by looking for negative throws
                    cursor.execute("""
                        SELECT team_number FROM throws t
                        JOIN legs l ON t.leg_id = l.id
                        WHERE l.sub_match_id = ? AND l.leg_number = ? AND t.score < 0
                        LIMIT 1
                    """, (sub_match_id, leg_num))
                    winning_throw_result = cursor.fetchone()
                    
                    if winning_throw_result:
                        leg_winner_team = winning_throw_result[0]
                    else:
                        # Fallback to stored winner_team if available
                        leg_winner_team = throw['winner_team']
                    
                    legs_with_throws[leg_num] = {
                        'leg_number': leg_num,
                        'winner_team': leg_winner_team,
                        'leg_total_rounds': throw['leg_total_rounds'],
                        'player_won_leg': leg_winner_team == sub_match_info['team_number'],
                        'player_throws': [],
                        'opponent_throws': []
                    }
            
            # Add throws to appropriate player/opponent lists
            for throw in player_throws:
                leg_num = throw['leg_number']
                legs_with_throws[leg_num]['player_throws'].append({
                    'round_number': throw['round_number'],
                    'score': throw['score'],
                    'remaining_score': throw['remaining_score'],
                    'darts_used': throw['darts_used']
                })
            
            for throw in opponent_throws:
                leg_num = throw['leg_number']
                legs_with_throws[leg_num]['opponent_throws'].append({
                    'round_number': throw['round_number'],
                    'score': throw['score'],
                    'remaining_score': throw['remaining_score'],
                    'darts_used': throw['darts_used']
                })
            
            # Calculate statistics for both players
            def calculate_player_stats(throws_list, team_number):
                total_throws = len(throws_list)
                scores = [t['score'] for t in throws_list if t['score'] >= 0]
                total_score = sum(scores)
                
                # Calculate total darts used for proper average calculation
                total_darts = 0
                for throw in throws_list:
                    if throw['score'] < 0:
                        # Checkout throw - use the dart count
                        total_darts += abs(throw['score'])
                    else:
                        # Regular throw - use 3 darts (or darts_used if available)
                        total_darts += throw.get('darts_used', 3)
                
                # Use the database player_avg instead of calculating it
                avg_score = sub_match_info['player_avg'] if team_number == sub_match_info['team_number'] else opponent_avg
                max_score = max(scores, default=0)
                legs_won = sum(1 for leg in legs_with_throws.values() if leg['winner_team'] == team_number)
                
                # Get checkout scores (what they actually scored to finish)
                checkout_scores = []
                for throw in throws_list:
                    if throw['score'] < 0:
                        # Find what score was needed to finish (remaining_score before the checkout)
                        cursor.execute("""
                            SELECT remaining_score
                            FROM throws 
                            WHERE leg_id = (SELECT id FROM legs WHERE sub_match_id = ? AND leg_number = ?)
                              AND team_number = ? AND round_number = ?
                        """, (sub_match_id, throw['leg_number'], team_number, throw['round_number'] - 1))
                        
                        checkout_result = cursor.fetchone()
                        if checkout_result:
                            checkout_score = checkout_result[0]  # This is what they scored to finish
                            checkout_scores.append(checkout_score)
                
                # Advanced statistics
                all_scores = scores + checkout_scores
                throws_100_139 = len([s for s in all_scores if 100 <= s < 140])
                throws_140_179 = len([s for s in all_scores if 140 <= s < 180])
                throws_180 = len([s for s in all_scores if s == 180])
                throws_100_plus_total = len([s for s in all_scores if s >= 100])
                throws_under_20 = len([s for s in scores if s < 20])
                throws_60_plus = len([s for s in all_scores if s >= 60])
                
                # Calculate "Första 9 pil" (first 3 rounds average across all legs)
                first_9_dart_scores = []
                for leg in legs_with_throws.values():
                    leg_throws_key = 'player_throws' if team_number == sub_match_info['team_number'] else 'opponent_throws'
                    leg_throws = leg[leg_throws_key]
                    # Take first 3 throws (rounds) from each leg
                    for i, throw in enumerate(leg_throws):
                        if i < 3 and throw['score'] >= 0:  # Only first 3 rounds and only positive scores
                            first_9_dart_scores.append(throw['score'])
                
                first_9_dart_avg = round(sum(first_9_dart_scores) / max(1, len(first_9_dart_scores)), 2) if first_9_dart_scores else 0
                
                checkouts = [-t['score'] for t in throws_list if t['score'] < 0]
                total_checkouts = len(checkouts)
                checkout_darts = sum(checkouts) if checkouts else 0
                
                # Calculate special leg achievements (only for legs won by this player)
                short_legs = 0  # 18 darts or fewer (6 rounds or fewer)
                short_legs_detail = []  # List of actual dart counts for short legs
                high_finishes = 0  # 100+ checkout
                high_finishes_detail = []  # List of actual checkout scores
                
                for leg in legs_with_throws.values():
                    if leg['winner_team'] == team_number:
                        # Count throws for this player in this leg
                        leg_throws_key = 'player_throws' if team_number == sub_match_info['team_number'] else 'opponent_throws'
                        leg_throws = leg.get(leg_throws_key, [])
                        
                        # Calculate total darts used in this leg
                        total_darts_in_leg = 0
                        checkout_score = 0
                        
                        for throw in leg_throws:
                            # Use darts_used field if available, otherwise default to 3
                            total_darts_in_leg += throw.get('darts_used', 3)
                        
                        # Check for short leg (18 darts or fewer)
                        if total_darts_in_leg <= 18:
                            short_legs += 1
                            short_legs_detail.append(total_darts_in_leg)
                        
                        # Check for high finish (100+)
                        # Get actual checkout score from the previous throw (remaining_score before checkout)
                        cursor.execute("""
                            SELECT t_prev.remaining_score as checkout_score
                            FROM throws t_checkout
                            JOIN legs l ON t_checkout.leg_id = l.id
                            JOIN throws t_prev ON t_prev.leg_id = l.id 
                              AND t_prev.team_number = t_checkout.team_number 
                              AND t_prev.round_number = t_checkout.round_number - 1
                            WHERE l.sub_match_id = ? AND l.leg_number = ? 
                              AND t_checkout.team_number = ? AND t_checkout.remaining_score = 0
                        """, (sub_match_id, leg['leg_number'], team_number))
                        
                        checkout_result = cursor.fetchone()
                        if checkout_result and checkout_result[0] >= 100:
                            high_finishes += 1
                            high_finishes_detail.append(checkout_result[0])
                
                return {
                    'total_throws': total_throws,
                    'total_score': total_score,
                    'average_score': avg_score,
                    'max_score': max_score,
                    'legs_won': legs_won,
                    'throws_100_139': throws_100_139,
                    'throws_140_179': throws_140_179,
                    'throws_180': throws_180,
                    'throws_100_plus_total': throws_100_plus_total,
                    'throws_under_20': throws_under_20,
                    'throws_60_plus': throws_60_plus,
                    'total_checkouts': total_checkouts,
                    'checkout_darts': checkout_darts,
                    'short_legs': short_legs,
                    'short_legs_detail': short_legs_detail,
                    'high_finishes': high_finishes,
                    'high_finishes_detail': high_finishes_detail,
                    'first_9_dart_avg': first_9_dart_avg
                }
            
            player_stats = calculate_player_stats(player_throws, sub_match_info['team_number'])
            opponent_stats = calculate_player_stats(opponent_throws, opposing_team_number)
            
            # Determine correct team names based on which team the player is on
            if sub_match_info['team_number'] == 1:
                player_team_name = sub_match_info['team1_name']
                opponent_team_name = sub_match_info['team2_name']
            else:
                player_team_name = sub_match_info['team2_name']
                opponent_team_name = sub_match_info['team1_name']

            # Create corrected sub_match_info with proper team order
            corrected_sub_match_info = dict(sub_match_info)
            corrected_sub_match_info['team1_name'] = player_team_name
            corrected_sub_match_info['team2_name'] = opponent_team_name
            
            return jsonify({
                'sub_match_info': corrected_sub_match_info,
                'player_name': player_name,
                'opponent_names': opponent_names,
                'teammate_names': teammate_names,
                'legs': list(legs_with_throws.values()),
                'player_statistics': {
                    **player_stats,
                    'legs_total': len(legs_with_throws)
                },
                'opponent_statistics': {
                    **opponent_stats,
                    'legs_total': len(legs_with_throws)
                }
            })
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/team/<team_name>/lineup')
def get_team_lineup(team_name):
    """Get team lineup prediction based on historical position data"""
    try:
        import sqlite3
        with sqlite3.connect(db.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Get filter parameters
            season = request.args.get('season')
            
            # Check if team exists
            cursor.execute("SELECT id FROM teams WHERE name = ?", (team_name,))
            team_result = cursor.fetchone()
            if not team_result:
                return jsonify({'error': 'Team not found'}), 404
            
            team_id = team_result['id']
            
            # Build WHERE clause for filtering
            where_conditions = ["(m.team1_id = ? OR m.team2_id = ?)"]
            params = [team_id, team_id]
            
            if season:
                where_conditions.append("m.season = ?")
                params.append(season)
            
            where_clause = " AND ".join(where_conditions)
            
            # Get position analysis for this team
            cursor.execute(f"""
                WITH position_data AS (
                    SELECT 
                        p.name as player_name,
                        sm.match_name,
                        sm.match_type,
                        smp.team_number,
                        CASE WHEN smp.team_number = 1 THEN t1.name ELSE t2.name END as player_team,
                        COUNT(*) as matches_in_position
                    FROM sub_match_participants smp
                    JOIN players p ON smp.player_id = p.id
                    JOIN sub_matches sm ON smp.sub_match_id = sm.id
                    JOIN matches m ON sm.match_id = m.id
                    JOIN teams t1 ON m.team1_id = t1.id
                    JOIN teams t2 ON m.team2_id = t2.id
                    WHERE {where_clause}
                      AND (CASE WHEN smp.team_number = 1 THEN t1.name ELSE t2.name END) = ?
                    GROUP BY p.name, sm.match_name, sm.match_type
                ),
                position_stats AS (
                    SELECT 
                        player_name,
                        CASE 
                            WHEN match_name LIKE '% AD%' OR match_name LIKE '%AD' THEN 'AD'
                            WHEN match_name LIKE '% Singles1%' THEN 'S1'
                            WHEN match_name LIKE '% Singles2%' THEN 'S2' 
                            WHEN match_name LIKE '% Singles3%' THEN 'S3'
                            WHEN match_name LIKE '% Singles4%' THEN 'S4'
                            WHEN match_name LIKE '% Singles5%' THEN 'S5'
                            WHEN match_name LIKE '% Singles6%' THEN 'S6'
                            WHEN match_name LIKE '% Doubles1%' THEN 'D1'
                            WHEN match_name LIKE '% Doubles2%' THEN 'D2'
                            WHEN match_name LIKE '% Doubles3%' THEN 'D3'
                            ELSE 'Unknown'
                        END as position,
                        SUM(matches_in_position) as total_matches
                    FROM position_data
                    GROUP BY player_name, position
                    HAVING position != 'Unknown'
                )
                SELECT 
                    position,
                    player_name,
                    total_matches,
                    ROW_NUMBER() OVER (PARTITION BY position ORDER BY total_matches DESC) as rank
                FROM position_stats
                ORDER BY position, total_matches DESC
            """, params + [team_name])
            
            position_data = cursor.fetchall()
            
            # Get total team matches for percentage calculation
            cursor.execute(f"""
                SELECT COUNT(DISTINCT m.id) as total_team_matches
                FROM matches m
                WHERE {where_clause}
            """, params)
            
            total_matches = cursor.fetchone()['total_team_matches']
            
            # Organize data by position
            positions = {}
            for row in position_data:
                position = row['position']
                if position not in positions:
                    positions[position] = {'players': [], 'total_position_matches': 0}
                
                # Calculate percentage for this position
                percentage = round((row['total_matches'] / total_matches) * 100, 1) if total_matches > 0 else 0
                
                player_data = {
                    'name': row['player_name'],
                    'matches': row['total_matches'],
                    'percentage': percentage,
                    'rank': row['rank']
                }
                
                positions[position]['players'].append(player_data)
                positions[position]['total_position_matches'] += row['total_matches']
            
            # Format response for frontend
            formatted_positions = {}
            for pos, data in positions.items():
                if pos.startswith('S'):  # Singles positions
                    formatted_positions[pos] = {
                        'top_player': data['players'][0] if data['players'] else None,
                        'all_players': data['players']
                    }
                else:  # Doubles positions (including AD)
                    # For doubles, we might want to show partnerships
                    formatted_positions[pos] = {
                        'players': data['players'][:3],  # Top 3 players for this position
                        'total_matches': data['total_position_matches']
                    }
            
            return jsonify({
                'team_name': team_name,
                'total_matches': total_matches,
                'season': season,
                'positions': formatted_positions
            })
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/match/<int:match_id>/legs')
def get_match_legs(match_id):
    """Get detailed leg information for a match"""
    try:
        import sqlite3
        with sqlite3.connect(db.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Get match info
            cursor.execute("""
                SELECT m.*, t1.name as team1_name, t2.name as team2_name
                FROM matches m
                JOIN teams t1 ON m.team1_id = t1.id
                JOIN teams t2 ON m.team2_id = t2.id
                WHERE m.id = ?
            """, (match_id,))
            
            match_info = cursor.fetchone()
            if not match_info:
                return jsonify({'error': 'Match not found'}), 404
            
            # Get all sub-matches with legs
            cursor.execute("""
                SELECT 
                    sm.*,
                    l.id as leg_id,
                    l.leg_number,
                    l.winner_team,
                    l.first_player_team,
                    l.total_rounds
                FROM sub_matches sm
                LEFT JOIN legs l ON sm.id = l.sub_match_id
                WHERE sm.match_id = ?
                ORDER BY sm.match_number, l.leg_number
            """, (match_id,))
            
            legs_data = cursor.fetchall()
            
            # Group by sub-match
            sub_matches = {}
            for row in legs_data:
                sm_id = row['id']
                if sm_id not in sub_matches:
                    sub_matches[sm_id] = {
                        'sub_match_id': sm_id,
                        'match_type': row['match_type'],
                        'match_name': row['match_name'],
                        'team1_legs': row['team1_legs'],
                        'team2_legs': row['team2_legs'],
                        'legs': []
                    }
                
                if row['leg_id']:  # Only add if leg exists
                    sub_matches[sm_id]['legs'].append({
                        'leg_number': row['leg_number'],
                        'winner_team': row['winner_team'],
                        'first_player_team': row['first_player_team'],
                        'total_rounds': row['total_rounds']
                    })
            
            return jsonify({
                'match_info': dict(match_info),
                'sub_matches': list(sub_matches.values())
            })
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500



if __name__ == '__main__':
    print("🎯 Starting GoldenStat Web Application...")
    print("📊 Open your browser to: http://localhost:3000")
    app.run(debug=True, host='0.0.0.0', port=3000)