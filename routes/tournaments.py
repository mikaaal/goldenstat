import os
import sqlite3
from flask import Blueprint, request, jsonify, render_template

tournaments_bp = Blueprint('tournaments', __name__)

TOURNAMENTS_DB_PATH = os.getenv('TOURNAMENTS_DATABASE_PATH', 'cups.db')


def get_tournaments_db():
    """Get a connection to the tournaments database"""
    conn = sqlite3.connect(TOURNAMENTS_DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


@tournaments_bp.route('/tournaments')
def tournaments_page():
    """Tournament default - player search"""
    return render_template('tournaments.html', cups_active=True)


@tournaments_bp.route('/tournaments/list')
def tournaments_list_page():
    """Tournament list"""
    return render_template('tournaments.html', cups_active=True)


@tournaments_bp.route('/tournaments/tournament')
def tournaments_tournament_page():
    """Tournament detail page"""
    return render_template('tournaments.html', cups_active=True)


@tournaments_bp.route('/tournaments/match')
def tournaments_match_page():
    """Tournament match detail page"""
    return render_template('tournaments.html', cups_active=True)


@tournaments_bp.route('/tournaments/players')
def tournaments_players_page():
    """Tournament player search page"""
    return render_template('tournaments.html', cups_active=True)


@tournaments_bp.route('/api/tournaments')
def api_tournaments():
    """List all tournaments with summary stats"""
    try:
        conn = get_tournaments_db()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT
                t.id, t.tdid, t.title, t.tournament_date, t.start_score,
                (SELECT COUNT(*) FROM participants p WHERE p.tournament_id = t.id) as participant_count,
                (SELECT COUNT(*) FROM cup_matches cm WHERE cm.tournament_id = t.id) as match_count,
                (SELECT COUNT(*) FROM legs l
                 JOIN cup_matches cm ON l.cup_match_id = cm.id
                 WHERE cm.tournament_id = t.id) as leg_count
            FROM tournaments t
            ORDER BY t.tournament_date DESC
        """)
        rows = cursor.fetchall()
        conn.close()
        return jsonify([dict(r) for r in rows])
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@tournaments_bp.route('/api/tournaments/<int:tid>')
def api_tournament_detail(tid):
    """Get full tournament details: info, participants, matches grouped by phase"""
    try:
        conn = get_tournaments_db()
        cursor = conn.cursor()

        # Tournament info
        cursor.execute("SELECT * FROM tournaments WHERE id = ?", (tid,))
        tournament = cursor.fetchone()
        if not tournament:
            conn.close()
            return jsonify({'error': 'Tournament not found'}), 404
        tournament = dict(tournament)

        # Participants with player names
        cursor.execute("""
            SELECT p.id, p.name, p.start_score,
                   GROUP_CONCAT(pl.name, ', ') as players
            FROM participants p
            LEFT JOIN participant_players pp ON pp.participant_id = p.id
            LEFT JOIN players pl ON pp.player_id = pl.id
            WHERE p.tournament_id = ?
            GROUP BY p.id
            ORDER BY COALESCE(pl.name, p.name)
        """, (tid,))
        participants = [dict(r) for r in cursor.fetchall()]

        # All matches with normalized player names
        cursor.execute("""
            SELECT cm.id, cm.phase, cm.phase_detail,
                   cm.participant1_id, cm.participant2_id,
                   cm.p1_legs_won, cm.p2_legs_won,
                   cm.p1_average, cm.p2_average,
                   cm.has_detail,
                   COALESCE(
                       (SELECT GROUP_CONCAT(pl.name, ' & ') FROM participant_players pp
                        JOIN players pl ON pp.player_id = pl.id
                        WHERE pp.participant_id = p1.id), p1.name) as p1_name,
                   COALESCE(
                       (SELECT GROUP_CONCAT(pl.name, ' & ') FROM participant_players pp
                        JOIN players pl ON pp.player_id = pl.id
                        WHERE pp.participant_id = p2.id), p2.name) as p2_name
            FROM cup_matches cm
            JOIN participants p1 ON cm.participant1_id = p1.id
            JOIN participants p2 ON cm.participant2_id = p2.id
            WHERE cm.tournament_id = ?
            ORDER BY cm.phase, cm.phase_detail, cm.id
        """, (tid,))
        all_matches = [dict(r) for r in cursor.fetchall()]
        conn.close()

        # Deduplicate RR matches (each pair appears twice with swapped sides)
        seen_rr_pairs = set()
        deduped_matches = []
        for m in all_matches:
            if m['phase'] == 'rr':
                pair = tuple(sorted([m['participant1_id'], m['participant2_id']]))
                if pair in seen_rr_pairs:
                    continue
                seen_rr_pairs.add(pair)
            deduped_matches.append(m)

        # Group matches by phase -> phase_detail
        matches = {'rr': [], 't': [], 's2': []}
        for phase_key in matches:
            phase_matches = [m for m in deduped_matches if m['phase'] == phase_key]
            groups = {}
            for m in phase_matches:
                g = m['phase_detail'] or '0'
                if g not in groups:
                    groups[g] = []
                groups[g].append(m)
            key_label = 'group' if phase_key == 'rr' else 'round'
            matches[phase_key] = [
                {key_label: g, 'matches': groups[g]}
                for g in sorted(groups.keys(), key=lambda x: int(x) if x.isdigit() else x)
            ]

        return jsonify({
            'tournament': tournament,
            'participants': participants,
            'matches': matches
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@tournaments_bp.route('/api/tournaments/match/<int:mid>')
def api_tournament_match_detail(mid):
    """Get match detail with legs and throws"""
    try:
        conn = get_tournaments_db()
        cursor = conn.cursor()

        # Match info with normalized player names and tournament start_score
        cursor.execute("""
            SELECT cm.*,
                   COALESCE(
                       (SELECT GROUP_CONCAT(pl.name, ' & ') FROM participant_players pp
                        JOIN players pl ON pp.player_id = pl.id
                        WHERE pp.participant_id = p1.id), p1.name) as p1_name,
                   COALESCE(
                       (SELECT GROUP_CONCAT(pl.name, ' & ') FROM participant_players pp
                        JOIN players pl ON pp.player_id = pl.id
                        WHERE pp.participant_id = p2.id), p2.name) as p2_name,
                   t.start_score, t.title as tournament_title
            FROM cup_matches cm
            JOIN participants p1 ON cm.participant1_id = p1.id
            JOIN participants p2 ON cm.participant2_id = p2.id
            JOIN tournaments t ON cm.tournament_id = t.id
            WHERE cm.id = ?
        """, (mid,))
        match = cursor.fetchone()
        if not match:
            conn.close()
            return jsonify({'error': 'Match not found'}), 404
        match = dict(match)

        # Legs with throws
        cursor.execute("""
            SELECT l.id, l.leg_number, l.winner_side, l.first_side, l.total_rounds
            FROM legs l
            WHERE l.cup_match_id = ?
            ORDER BY l.leg_number
        """, (mid,))
        legs_rows = cursor.fetchall()

        legs = []
        for leg_row in legs_rows:
            leg = dict(leg_row)
            cursor.execute("""
                SELECT side_number, round_number, score, remaining_score, darts_used
                FROM throws
                WHERE leg_id = ?
                ORDER BY round_number, side_number
            """, (leg['id'],))
            leg['throws'] = [dict(t) for t in cursor.fetchall()]
            del leg['id']  # Don't expose internal leg id
            legs.append(leg)

        conn.close()
        return jsonify({
            'match': match,
            'legs': legs
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@tournaments_bp.route('/api/tournaments/players')
def api_tournament_players():
    """Get all unique player names across tournaments for autocomplete"""
    try:
        conn = get_tournaments_db()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT DISTINCT pl.name
            FROM players pl
            JOIN participant_players pp ON pp.player_id = pl.id
            JOIN participants pa ON pa.id = pp.participant_id
            JOIN cup_matches cm ON cm.participant1_id = pa.id OR cm.participant2_id = pa.id
            ORDER BY pl.name
        """)
        players = [row[0] for row in cursor.fetchall()]
        conn.close()
        return jsonify(players)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@tournaments_bp.route('/api/tournaments/player/<path:player_name>')
def api_tournament_player_matches(player_name):
    """Get all tournament matches for a specific player"""
    try:
        from urllib.parse import unquote
        player_name = unquote(player_name)

        conn = get_tournaments_db()
        cursor = conn.cursor()

        # Find all matches where this player participated (either side)
        cursor.execute("""
            SELECT cm.id, cm.phase, cm.phase_detail,
                   cm.p1_legs_won, cm.p2_legs_won,
                   cm.p1_average, cm.p2_average,
                   cm.has_detail,
                   cm.participant1_id, cm.participant2_id,
                   COALESCE(
                       (SELECT GROUP_CONCAT(pl.name, ' & ') FROM participant_players pp
                        JOIN players pl ON pp.player_id = pl.id
                        WHERE pp.participant_id = p1.id), p1.name) as p1_name,
                   COALESCE(
                       (SELECT GROUP_CONCAT(pl.name, ' & ') FROM participant_players pp
                        JOIN players pl ON pp.player_id = pl.id
                        WHERE pp.participant_id = p2.id), p2.name) as p2_name,
                   t.title as tournament_title,
                   t.tournament_date,
                   t.start_score,
                   t.id as tournament_id
            FROM cup_matches cm
            JOIN participants p1 ON cm.participant1_id = p1.id
            JOIN participants p2 ON cm.participant2_id = p2.id
            JOIN tournaments t ON cm.tournament_id = t.id
            WHERE cm.participant1_id IN (
                SELECT pp.participant_id FROM participant_players pp
                JOIN players pl ON pp.player_id = pl.id WHERE pl.name = ?
            ) OR cm.participant2_id IN (
                SELECT pp.participant_id FROM participant_players pp
                JOIN players pl ON pp.player_id = pl.id WHERE pl.name = ?
            )
            ORDER BY t.tournament_date DESC, cm.phase, cm.phase_detail, cm.id
        """, (player_name, player_name))
        all_matches = [dict(r) for r in cursor.fetchall()]

        # Get max round per phase per tournament for knockout round naming
        cursor.execute("""
            SELECT tournament_id, phase, MAX(CAST(phase_detail AS INTEGER)) as max_round
            FROM cup_matches
            WHERE phase IN ('t', 's2')
            GROUP BY tournament_id, phase
        """)
        max_rounds = {(r[0], r[1]): r[2] for r in cursor.fetchall()}
        conn.close()

        def knockout_round_name(phase, phase_detail, tournament_id):
            max_r = max_rounds.get((tournament_id, phase))
            if max_r is None:
                return phase
            pos_from_end = max_r - int(phase_detail)
            names = {0: 'Final', 1: 'Semifinal', 2: 'Kvartsfinal',
                     3: '8-delsfinal', 4: '16-delsfinal', 5: '32-delsfinal'}
            return names.get(pos_from_end, f'Omg\u00e5ng {pos_from_end + 1}')

        # Deduplicate RR matches and add round labels
        seen_rr_pairs = set()
        matches = []
        for m in all_matches:
            if m['phase'] == 'rr':
                pair = tuple(sorted([m['participant1_id'], m['participant2_id']]))
                if pair in seen_rr_pairs:
                    continue
                seen_rr_pairs.add(pair)
            if m['phase'] in ('t', 's2'):
                prefix = 'B-' if m['phase'] == 's2' else ''
                m['phase_label'] = prefix + knockout_round_name(m['phase'], m['phase_detail'], m['tournament_id'])
            else:
                m['phase_label'] = 'Poolspel'
            matches.append(m)

        return jsonify({
            'player_name': player_name,
            'matches': matches
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500
