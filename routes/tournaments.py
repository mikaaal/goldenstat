import os
import sqlite3
from flask import Blueprint, request, jsonify, render_template
from collections import defaultdict

tournaments_bp = Blueprint('tournaments', __name__)

TOURNAMENTS_DB_PATH = os.getenv('TOURNAMENTS_DATABASE_PATH', 'cups.db')


def calculate_fun_facts(matches, player_name):
    """Calculate personalized fun facts for a player based on their matches."""
    if not matches:
        return []

    import re
    fun_facts = []

    # Track opponent stats (singles only)
    opponent_record = defaultdict(lambda: {'wins': 0, 'losses': 0})

    # Track organizer participations (count unique tournaments per organizer)
    organizer_tournaments = defaultdict(set)

    # Track best match
    best_match = {'avg': 0, 'opponent': '', 'tournament': '', 'date': ''}
    first_match = None

    # Track best placement - separate for singles and doubles
    # Score: win in phase is better than loss, higher phase is better
    # Final win = 12, Final loss = 11, Semi win = 10, Semi loss = 9, etc.
    # B-slutspel counts but lower than A
    best_singles_placement = {'score': 0, 'text': '', 'tournament': '', 'date': '', 'won': False}
    best_doubles_placement = {'score': 0, 'text': '', 'tournament': '', 'date': '', 'won': False}

    def get_phase_score(phase_label, won, is_b_slutspel):
        """Calculate a score for ranking placements.

        Ranking logic:
        - A-Final vinst = 13, A-Final förlust = 12
        - A-Semifinal vinst = 11, A-Semifinal förlust = 10
        - B-Final vinst = 11 (same as A-Semi vinst)
        - A-Kvartsfinal vinst = 9, A-Kvartsfinal förlust = 8
        - B-Final förlust = 9, B-Semifinal vinst = 9
        """
        base_scores = {
            'Final': 6, 'Semifinal': 5, 'Kvartsfinal': 4,
            '8-delsfinal': 3, '16-delsfinal': 2, '32-delsfinal': 1, 'Poolspel': 0
        }
        # Strip B- prefix for lookup
        clean_label = phase_label.replace('B-', '') if phase_label else ''
        base = base_scores.get(clean_label, 0)
        if base == 0:
            return 0
        # Double it and add 1 for win
        score = base * 2 + (1 if won else 0)
        # B-slutspel: subtract 2 (B-Final vinst = A-Semifinal vinst level)
        if is_b_slutspel:
            score = max(1, score - 2)
        return score

    # Track streaks
    current_streak = 0
    best_streak = {'count': 0, 'tournament': ''}
    last_tournament = None
    last_tournament_name = ''

    # Doubles pattern
    doubles_pattern = re.compile(r'\s+&\s+|\s*/\s*|\s+\+\s+|\s+och\s+', re.IGNORECASE)

    # Extract organizer from tournament title
    def get_organizer(title):
        if not title:
            return 'Okänd'
        title_lower = title.lower()
        # Known organizers
        if "mini's" in title_lower or "minis" in title_lower or "mini´s" in title_lower:
            return "MiNi's"
        if "east" in title_lower:
            return "East"
        if "stdf" in title_lower:
            return "StDF"
        if "sofo" in title_lower:
            return "SoFo House"
        if "ssdc" in title_lower:
            return "SSDC"
        if "cobra" in title_lower:
            return "Cobra"
        if "oilers" in title_lower:
            return "Oilers"
        # Default: first word
        return title.split()[0] if title.split() else 'Okänd'

    for m in sorted(matches, key=lambda x: x.get('tournament_date') or ''):
        is_p1 = player_name in (m.get('p1_name') or '')
        p_legs = m['p1_legs_won'] if is_p1 else m['p2_legs_won']
        o_legs = m['p2_legs_won'] if is_p1 else m['p1_legs_won']
        avg = m['p1_average'] if is_p1 else m['p2_average']
        opponent = m['p2_name'] if is_p1 else m['p1_name']

        # Skip matches with missing leg data
        if p_legs is None or o_legs is None:
            continue

        won = p_legs > o_legs

        is_singles = not doubles_pattern.search(m.get('p1_name') or '') and not doubles_pattern.search(m.get('p2_name') or '')

        # Track first match
        if first_match is None:
            first_match = m

        # Organizer participations (count unique tournaments)
        organizer = get_organizer(m.get('tournament_title', ''))
        organizer_tournaments[organizer].add(m.get('tournament_id'))

        # Best match (singles only)
        if is_singles and avg and avg > best_match['avg']:
            best_match = {
                'avg': avg,
                'opponent': opponent,
                'tournament': m.get('tournament_title', ''),
                'date': (m.get('tournament_date') or '')[:10]
            }

        # Opponent record (singles only)
        if is_singles and opponent:
            if won:
                opponent_record[opponent]['wins'] += 1
            elif o_legs > p_legs:
                opponent_record[opponent]['losses'] += 1

        # Best placement tracking
        phase_label = m.get('phase_label', 'Poolspel')
        is_b_slutspel = phase_label.startswith('B-')
        phase_score = get_phase_score(phase_label, won, is_b_slutspel)

        # Prestige bonus for important tournaments
        tournament_title = (m.get('tournament_title') or '').lower()
        if 'stdf' in tournament_title or 'dm ' in tournament_title or tournament_title.startswith('dm '):
            phase_score += 5  # StDF/DM = Sveriges bästa spelare, alltid högst prestige
        elif 'ssdc' in tournament_title:
            phase_score += 3  # SSDC är också prestigefullt
        else:
            # Bonus för stora turneringar (endast icke-StDF/DM)
            num_participants = m.get('num_participants') or 0
            if num_participants >= 40:
                phase_score += 2  # 40+ deltagare
            elif num_participants >= 24:
                phase_score += 1  # 24+ deltagare

        if phase_score > 0:
            placement_data = {
                'score': phase_score,
                'text': f"{phase_label}{' (vinst)' if won else ''}",
                'tournament': m.get('tournament_title', ''),
                'date': (m.get('tournament_date') or '')[:10],
                'won': won
            }
            if is_singles:
                if phase_score >= best_singles_placement['score']:
                    best_singles_placement = placement_data
            else:
                if phase_score >= best_doubles_placement['score']:
                    best_doubles_placement = placement_data

        # Win streak tracking
        current_tournament = m.get('tournament_id')
        if current_tournament != last_tournament:
            if current_streak > best_streak['count']:
                best_streak = {'count': current_streak, 'tournament': last_tournament_name}
            current_streak = 0
        last_tournament = current_tournament
        last_tournament_name = m.get('tournament_title', '')

        if won:
            current_streak += 1
        else:
            if current_streak > best_streak['count']:
                best_streak = {'count': current_streak, 'tournament': last_tournament_name}
            current_streak = 0

    # Check final streak
    if current_streak > best_streak['count']:
        best_streak = {'count': current_streak, 'tournament': last_tournament_name}

    # Generate fun facts

    # 1. First tournament
    if first_match:
        date = (first_match.get('tournament_date') or '')[:10]
        tournament = first_match.get('tournament_title', '')
        fun_facts.append({
            'emoji': '📅',
            'title': 'Första cupen',
            'text': f"{tournament.split(',')[0]}",
            'detail': date
        })

    # 2. Best match
    if best_match['avg'] > 0:
        fun_facts.append({
            'emoji': '🌟',
            'title': 'Bästa matchen',
            'text': f"{best_match['avg']:.1f} i snitt mot {best_match['opponent']}",
            'detail': f"{best_match['tournament'].split(',')[0]} ({best_match['date']})"
        })

    # 3. Best placement - prefer singles, fall back to doubles
    best_placement = best_singles_placement if best_singles_placement['score'] > 0 else best_doubles_placement
    if best_placement['score'] > 0:
        is_doubles = best_placement == best_doubles_placement and best_singles_placement['score'] == 0
        title = 'Bästa placering (dubbel)' if is_doubles else 'Bästa placering'
        fun_facts.append({
            'emoji': '🏆',
            'title': title,
            'text': best_placement['text'],
            'detail': f"{best_placement['tournament'].split(',')[0]} ({best_placement['date']})"
        })

    # 4. Nemesis (lost most against, min 2 losses)
    nemesis = None
    for opp, record in opponent_record.items():
        if record['losses'] >= 2:
            if nemesis is None or record['losses'] > nemesis['losses']:
                nemesis = {'name': opp, 'wins': record['wins'], 'losses': record['losses']}

    if nemesis and nemesis['losses'] > nemesis['wins']:
        fun_facts.append({
            'emoji': '😈',
            'title': 'Nemesis',
            'text': f"{nemesis['name']}",
            'detail': f"{nemesis['wins']}-{nemesis['losses']} i inbördes möten"
        })

    # 5. Favorite opponent (won most against, min 2 wins)
    favorite = None
    for opp, record in opponent_record.items():
        if record['wins'] >= 2:
            if favorite is None or record['wins'] > favorite['wins']:
                if record['wins'] > record['losses']:
                    favorite = {'name': opp, 'wins': record['wins'], 'losses': record['losses']}

    if favorite:
        fun_facts.append({
            'emoji': '💪',
            'title': 'Favoritmotståndare',
            'text': f"{favorite['name']}",
            'detail': f"{favorite['wins']}-{favorite['losses']} i inbördes möten"
        })

    # 6. Most met opponent
    most_met = None
    for opp, record in opponent_record.items():
        total = record['wins'] + record['losses']
        if total >= 3:
            if most_met is None or total > most_met['total']:
                most_met = {'name': opp, 'wins': record['wins'], 'losses': record['losses'], 'total': total}

    if most_met and (not nemesis or most_met['name'] != nemesis['name']) and (not favorite or most_met['name'] != favorite['name']):
        fun_facts.append({
            'emoji': '🤝',
            'title': 'Mött flest gånger',
            'text': f"{most_met['name']}",
            'detail': f"{most_met['total']} matcher ({most_met['wins']}-{most_met['losses']})"
        })

    # 7. Favorite organizer (most tournament participations)
    if organizer_tournaments:
        fav_organizer = max(organizer_tournaments.items(), key=lambda x: len(x[1]))
        num_tournaments = len(fav_organizer[1])
        if num_tournaments >= 3:
            fun_facts.append({
                'emoji': '🎪',
                'title': 'Stamkund',
                'text': f"{fav_organizer[0]}",
                'detail': f"{num_tournaments} turneringar"
            })

    # 8. Best win streak
    if best_streak['count'] >= 4:
        fun_facts.append({
            'emoji': '🔥',
            'title': 'Längsta vinstsvit',
            'text': f"{best_streak['count']} raka vinster",
            'detail': best_streak['tournament'].split(',')[0]
        })

    # 9. Number of unique opponents
    num_opponents = len(opponent_record)
    if num_opponents >= 10:
        fun_facts.append({
            'emoji': '⚔️',
            'title': 'Mött',
            'text': f"{num_opponents} olika motståndare",
            'detail': 'i singelmatcher'
        })

    return fun_facts[:6]  # Return max 6 fun facts


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
                 WHERE cm.tournament_id = t.id) as leg_count,
                (SELECT COUNT(*) FROM participants px WHERE px.tournament_id = t.id AND px.start_score != t.start_score) > 0 as has_hcp,
                (SELECT MAX(cnt) FROM (
                    SELECT COUNT(*) as cnt FROM participant_players pp
                    JOIN participants p ON pp.participant_id = p.id
                    WHERE p.tournament_id = t.id GROUP BY pp.participant_id
                )) > 1 as is_doubles
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
            WHERE pl.id NOT IN (SELECT alias_player_id FROM cup_player_mappings)
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
                   t.id as tournament_id,
                   p1.start_score as p1_start_score,
                   p2.start_score as p2_start_score,
                   (SELECT COUNT(*) FROM participants px WHERE px.tournament_id = t.id) as num_participants,
                   (SELECT COUNT(*) FROM participants px WHERE px.tournament_id = t.id AND px.start_score != t.start_score) > 0 as tournament_has_hcp,
                   (SELECT MAX(cnt) FROM (
                       SELECT COUNT(*) as cnt FROM participant_players pp
                       JOIN participants p ON pp.participant_id = p.id
                       WHERE p.tournament_id = t.id GROUP BY pp.participant_id
                   )) > 1 as tournament_is_doubles
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

        # Calculate fun facts
        fun_facts = calculate_fun_facts(matches, player_name)

        return jsonify({
            'player_name': player_name,
            'matches': matches,
            'fun_facts': fun_facts
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500
