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
    opponent_record = defaultdict(lambda: {'wins': 0, 'losses': 0, 'tournament_ids': set()})
    opponent_last_met = {}  # track last match date per opponent
    opponent_averages = defaultdict(list)  # avg per match against each opponent
    all_averages = []  # all player averages for calculating overall mean
    opponent_playoff_record = defaultdict(lambda: {'wins': 0, 'losses': 0, 'tournament_ids': set()})  # knockout/playoff record per opponent
    opponent_tight_matches = defaultdict(int)  # matches decided by 1 leg per opponent
    whitewash_count = 0  # matches won without losing a leg
    whitewash_tournament_ids = set()
    finals_tournament_ids = set()
    singles_wins = 0
    singles_losses = 0
    finals_played = 0
    finals_won = 0
    doubles_partners = defaultdict(lambda: {'count': 0, 'tournament_ids': set()})  # partner stats
    tournament_ids = set()
    last_match = None

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
    best_streak = {'count': 0, 'tournament': '', 'tournament_id': None}
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

        # Check if this is a standard 501 match (301 has double-in which skews averages)
        player_start = m.get('p1_start_score' if is_p1 else 'p2_start_score') or m.get('start_score') or 501
        is_standard = player_start >= 501

        # Track first/last match
        if first_match is None:
            first_match = m
        last_match = m

        # Track unique tournaments
        tournament_ids.add(m.get('tournament_id'))

        # Organizer participations (count unique tournaments)
        organizer = get_organizer(m.get('tournament_title', ''))
        organizer_tournaments[organizer].add(m.get('tournament_id'))

        # Track doubles partners
        if not is_singles:
            p1_name = m.get('p1_name') or ''
            p2_name = m.get('p2_name') or ''
            # Find player's team name (the one containing player_name)
            my_team = p1_name if player_name in p1_name else p2_name
            # Split team to find partner(s)
            parts = doubles_pattern.split(my_team)
            for part in parts:
                part = part.strip()
                if part and part != player_name:
                    doubles_partners[part]['count'] += 1
                    doubles_partners[part]['tournament_ids'].add(m.get('tournament_id'))

        # Best match (singles only, standard 501 only)
        if is_singles and is_standard and avg and avg > best_match['avg']:
            best_match = {
                'avg': avg,
                'opponent': opponent,
                'tournament': m.get('tournament_title', ''),
                'date': (m.get('tournament_date') or '')[:10],
                'tournament_id': m.get('tournament_id')
            }

        # Whitewash tracking (singles only)
        if is_singles and won and o_legs == 0:
            whitewash_count += 1
            whitewash_tournament_ids.add(m.get('tournament_id'))

        # Finals tracking (singles only)
        if is_singles:
            phase = m.get('phase_label', '')
            if phase and phase.replace('B-', '') == 'Final':
                finals_played += 1
                finals_tournament_ids.add(m.get('tournament_id'))
                if won:
                    finals_won += 1

        # Opponent record (singles only)
        if is_singles and opponent:
            opponent_record[opponent]['tournament_ids'].add(m.get('tournament_id'))
            opponent_last_met[opponent] = m.get('tournament_date') or ''
            if won:
                opponent_record[opponent]['wins'] += 1
                singles_wins += 1
            elif o_legs > p_legs:
                opponent_record[opponent]['losses'] += 1
                singles_losses += 1
            # Track averages per opponent (standard 501 only)
            if is_standard and avg and avg > 0:
                opponent_averages[opponent].append(avg)
                all_averages.append(avg)
            # Track tight matches (decided by 1 leg)
            if abs(p_legs - o_legs) == 1:
                opponent_tight_matches[opponent] += 1
            # Track playoff/knockout record (non-pool matches)
            phase_label_check = m.get('phase_label', 'Poolspel')
            if phase_label_check and phase_label_check != 'Poolspel':
                opponent_playoff_record[opponent]['tournament_ids'].add(m.get('tournament_id'))
                if won:
                    opponent_playoff_record[opponent]['wins'] += 1
                elif o_legs > p_legs:
                    opponent_playoff_record[opponent]['losses'] += 1

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
                'tournament_id': m.get('tournament_id'),
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
                best_streak = {'count': current_streak, 'tournament': last_tournament_name, 'tournament_id': last_tournament}
            current_streak = 0
        last_tournament = current_tournament
        last_tournament_name = m.get('tournament_title', '')

        if won:
            current_streak += 1
        else:
            if current_streak > best_streak['count']:
                best_streak = {'count': current_streak, 'tournament': last_tournament_name, 'tournament_id': current_tournament}
            current_streak = 0

    # Check final streak
    if current_streak > best_streak['count']:
        best_streak = {'count': current_streak, 'tournament': last_tournament_name, 'tournament_id': last_tournament}

    # Generate fun facts

    # 1. Best match
    if best_match['avg'] > 0:
        fun_facts.append({
            'emoji': '🌟',
            'title': 'Bästa matchen',
            'text': f"{best_match['avg']:.1f} i snitt mot {best_match['opponent']}",
            'detail': f"{best_match['tournament'].split(',')[0]} ({best_match['date']})",
            'filter_tournaments': [best_match['tournament_id']] if best_match.get('tournament_id') else None
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
            'detail': f"{best_placement['tournament'].split(',')[0]} ({best_placement['date']})",
            'filter_tournaments': [best_placement['tournament_id']] if best_placement.get('tournament_id') else None
        })

    # 4. Nemesis (lost most against, min 2 losses, prefer recently met)
    nemesis = None
    for opp, record in opponent_record.items():
        if record['losses'] >= 2:
            if nemesis is None or record['losses'] > nemesis['losses'] or (record['losses'] == nemesis['losses'] and opponent_last_met.get(opp, '') > nemesis.get('last_met', '')):
                nemesis = {'name': opp, 'wins': record['wins'], 'losses': record['losses'], 'tournament_ids': list(record['tournament_ids']), 'last_met': opponent_last_met.get(opp, '')}

    if nemesis and nemesis['losses'] > nemesis['wins']:
        fun_facts.append({
            'emoji': '😈',
            'title': 'Nemesis',
            'text': f"{nemesis['name']}",
            'detail': f"{nemesis['wins']}-{nemesis['losses']} i inbördes möten",
            'filter_tournaments': nemesis['tournament_ids']
        })

    # 5. Favorite opponent (won most against, min 2 wins, prefer recently met)
    favorite = None
    for opp, record in opponent_record.items():
        if record['wins'] >= 2:
            if record['wins'] > record['losses']:
                if favorite is None or record['wins'] > favorite['wins'] or (record['wins'] == favorite['wins'] and opponent_last_met.get(opp, '') > favorite.get('last_met', '')):
                    favorite = {'name': opp, 'wins': record['wins'], 'losses': record['losses'], 'tournament_ids': list(record['tournament_ids']), 'last_met': opponent_last_met.get(opp, '')}

    if favorite:
        fun_facts.append({
            'emoji': '💪',
            'title': 'Favoritmotståndare',
            'text': f"{favorite['name']}",
            'detail': f"{favorite['wins']}-{favorite['losses']} i inbördes möten",
            'filter_tournaments': favorite['tournament_ids']
        })

    # 6. Most met opponent (prefer recently met)
    most_met = None
    for opp, record in opponent_record.items():
        total = record['wins'] + record['losses']
        if total >= 3:
            if most_met is None or total > most_met['total'] or (total == most_met['total'] and opponent_last_met.get(opp, '') > most_met.get('last_met', '')):
                most_met = {'name': opp, 'wins': record['wins'], 'losses': record['losses'], 'total': total, 'tournament_ids': list(record['tournament_ids']), 'last_met': opponent_last_met.get(opp, '')}

    if most_met and (not nemesis or most_met['name'] != nemesis['name']) and (not favorite or most_met['name'] != favorite['name']):
        fun_facts.append({
            'emoji': '🤝',
            'title': 'Mött flest gånger',
            'text': f"{most_met['name']}",
            'detail': f"{most_met['total']} matcher ({most_met['wins']}-{most_met['losses']})",
            'filter_tournaments': most_met['tournament_ids']
        })

    # 7. Most even opponent (min 4 matches, closest to 50/50, prefer recently met)
    even_opponent = None
    even_best_diff = float('inf')
    for opp, record in opponent_record.items():
        total = record['wins'] + record['losses']
        if total >= 4:
            diff = abs(record['wins'] - record['losses'])
            if diff < even_best_diff or (diff == even_best_diff and (total > (even_opponent or {}).get('total', 0) or (total == (even_opponent or {}).get('total', 0) and opponent_last_met.get(opp, '') > (even_opponent or {}).get('last_met', '')))):
                even_best_diff = diff
                even_opponent = {'name': opp, 'wins': record['wins'], 'losses': record['losses'], 'total': total, 'tournament_ids': list(record['tournament_ids']), 'last_met': opponent_last_met.get(opp, '')}

    if even_opponent and even_best_diff <= 1:
        fun_facts.append({
            'emoji': '🎯',
            'title': 'Jämnast motståndare',
            'text': f"{even_opponent['name']}",
            'detail': f"{even_opponent['wins']}-{even_opponent['losses']} i {even_opponent['total']} matcher",
            'filter_tournaments': even_opponent['tournament_ids']
        })

    # 8. "Levels up" against - opponent where player performs most above their overall average (min 4 matches, prefer recently met)
    overall_avg = sum(all_averages) / len(all_averages) if all_averages else 0
    levels_up_opponent = None
    if overall_avg > 0:
        for opp, avgs in opponent_averages.items():
            if len(avgs) >= 4:
                mean_avg = sum(avgs) / len(avgs)
                diff = mean_avg - overall_avg
                if diff > 0 and (levels_up_opponent is None or diff > levels_up_opponent['diff'] or (diff == levels_up_opponent['diff'] and opponent_last_met.get(opp, '') > levels_up_opponent.get('last_met', ''))):
                    levels_up_opponent = {'name': opp, 'avg': mean_avg, 'diff': diff, 'matches': len(avgs), 'last_met': opponent_last_met.get(opp, '')}

    if levels_up_opponent:
        fun_facts.append({
            'emoji': '📈',
            'title': 'Vässar till sig mot',
            'text': f"{levels_up_opponent['name']}",
            'detail': f"{levels_up_opponent['avg']:.1f} snitt (+{levels_up_opponent['diff']:.1f} över normalt)",
            'filter_tournaments': list(opponent_record[levels_up_opponent['name']]['tournament_ids'])
        })

    # 9. Undefeated against (min 3 wins, 0 losses, prefer recently met)
    undefeated = None
    for opp, record in opponent_record.items():
        if record['wins'] >= 3 and record['losses'] == 0:
            if undefeated is None or record['wins'] > undefeated['wins'] or (record['wins'] == undefeated['wins'] and opponent_last_met.get(opp, '') > undefeated.get('last_met', '')):
                undefeated = {'name': opp, 'wins': record['wins'], 'tournament_ids': list(record['tournament_ids']), 'last_met': opponent_last_met.get(opp, '')}

    if undefeated:
        fun_facts.append({
            'emoji': '👻',
            'title': 'Obesegrad mot',
            'text': f"{undefeated['name']}",
            'detail': f"{undefeated['wins']}-0 i inbördes möten",
            'filter_tournaments': undefeated['tournament_ids']
        })

    # 10. Playoff opponent (most meetings in knockout phases, min 2, prefer recently met)
    if opponent_playoff_record:
        playoff_opp = max(opponent_playoff_record.items(), key=lambda x: (x[1]['wins'] + x[1]['losses'], opponent_last_met.get(x[0], '')))
        total_playoff = playoff_opp[1]['wins'] + playoff_opp[1]['losses']
        if total_playoff >= 2:
            opp_name = playoff_opp[0]
            fun_facts.append({
                'emoji': '🏟️',
                'title': 'Slutspelsmotståndare',
                'text': f"{opp_name}",
                'detail': f"{total_playoff} slutspelsmöten ({playoff_opp[1]['wins']}-{playoff_opp[1]['losses']})",
                'filter_tournaments': list(playoff_opp[1]['tournament_ids'])
            })

    # 11. "Drops level" against - opponent where player performs most below their overall average (min 4 matches, prefer recently met)
    drops_level_opponent = None
    if overall_avg > 0:
        for opp, avgs in opponent_averages.items():
            if len(avgs) >= 4:
                mean_avg = sum(avgs) / len(avgs)
                diff = overall_avg - mean_avg
                if diff > 0 and (drops_level_opponent is None or diff > drops_level_opponent['diff'] or (diff == drops_level_opponent['diff'] and opponent_last_met.get(opp, '') > drops_level_opponent.get('last_met', ''))):
                    drops_level_opponent = {'name': opp, 'avg': mean_avg, 'diff': diff, 'matches': len(avgs), 'last_met': opponent_last_met.get(opp, '')}

    if drops_level_opponent:
        fun_facts.append({
            'emoji': '📉',
            'title': 'Tappar nivå mot',
            'text': f"{drops_level_opponent['name']}",
            'detail': f"{drops_level_opponent['avg']:.1f} snitt (-{drops_level_opponent['diff']:.1f} under normalt)",
            'filter_tournaments': list(opponent_record[drops_level_opponent['name']]['tournament_ids'])
        })

    # 12. Tight matches! - opponent with most matches decided by 1 leg (min 3, prefer recently met)
    if opponent_tight_matches:
        tight_opp = max(opponent_tight_matches.items(), key=lambda x: (x[1], opponent_last_met.get(x[0], '')))
        if tight_opp[1] >= 3:
            opp_name = tight_opp[0]
            record = opponent_record[opp_name]
            fun_facts.append({
                'emoji': '😰',
                'title': 'Nagelbitare',
                'text': f"{opp_name}",
                'detail': f"{tight_opp[1]} matcher avgjorda med 1 leg ({record['wins']}-{record['losses']})",
                'filter_tournaments': list(record['tournament_ids'])
            })

    # 13. Favorite organizer (most tournament participations)
    if organizer_tournaments:
        fav_organizer = max(organizer_tournaments.items(), key=lambda x: len(x[1]))
        num_tournaments = len(fav_organizer[1])
        if num_tournaments >= 3:
            fun_facts.append({
                'emoji': '🎪',
                'title': 'Stamkund',
                'text': f"{fav_organizer[0]}",
                'detail': f"{num_tournaments} turneringar",
                'filter_tournaments': list(fav_organizer[1])
            })

    # 13. Best win streak
    if best_streak['count'] >= 4:
        fun_facts.append({
            'emoji': '🔥',
            'title': 'Längsta vinstsvit',
            'text': f"{best_streak['count']} raka vinster",
            'detail': best_streak['tournament'].split(',')[0],
            'filter_tournaments': [best_streak['tournament_id']] if best_streak.get('tournament_id') else None
        })

    # 14. Number of unique opponents
    num_opponents = len(opponent_record)
    if num_opponents >= 10:
        fun_facts.append({
            'emoji': '⚔️',
            'title': 'Mött',
            'text': f"{num_opponents} olika motståndare",
            'detail': 'i singelmatcher'
        })

    # 15. Whitewash wins (won without losing a leg)
    if whitewash_count >= 2:
        fun_facts.append({
            'emoji': '🧹',
            'title': 'Nollat motståndare',
            'text': f"{whitewash_count} matcher",
            'detail': 'vinster utan att förlora ett leg',
            'filter_tournaments': list(whitewash_tournament_ids)
        })

    # 16. Finals specialist
    if finals_played >= 2:
        fun_facts.append({
            'emoji': '🏅',
            'title': 'Finalspecialist',
            'text': f"{finals_won} vinster av {finals_played} finaler",
            'detail': f"{finals_won}/{finals_played} vunna",
            'filter_tournaments': list(finals_tournament_ids)
        })

    # 17. Win percentage s (min 10 matches)
    total_singles = singles_wins + singles_losses
    if total_singles >= 10:
        win_pct = (singles_wins / total_singles) * 100
        fun_facts.append({
            'emoji': '📊',
            'title': 'Vinstprocent',
            'text': f"{win_pct:.0f}%",
            'detail': f"{singles_wins} vinster, {singles_losses} förluster i singel"
        })

    # 18. Doubles partner (min 2 matches together)
    if doubles_partners:
        best_partner = max(doubles_partners.items(), key=lambda x: x[1]['count'])
        if best_partner[1]['count'] >= 2:
            count = best_partner[1]['count']
            t_ids = list(best_partner[1]['tournament_ids'])
            fun_facts.append({
                'emoji': '👯',
                'title': 'Dubbelpartner',
                'text': f"{best_partner[0]}",
                'detail': f"{count} matcher tillsammans",
                'filter_tournaments': t_ids
            })

    # 19. Cup veteran (years active)
    if first_match and last_match:
        first_date = (first_match.get('tournament_date') or '')[:4]
        last_date = (last_match.get('tournament_date') or '')[:4]
        if first_date and last_date and first_date != last_date:
            years = int(last_date) - int(first_date)
            if years >= 2:
                fun_facts.append({
                    'emoji': '📆',
                    'title': 'Cupveteran',
                    'text': f"{years} år aktiv",
                    'detail': f"{first_date}–{last_date}"
                })

    # 20. Tournaments played
    num_tournaments = len(tournament_ids)
    if num_tournaments >= 5:
        fun_facts.append({
            'emoji': '🎲',
            'title': 'Turneringar',
            'text': f"{num_tournaments} spelade",
            'detail': 'unika turneringar'
        })

    return fun_facts


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

        # Calculate win/loss leg averages for each participant using same logic as series matches
        def calculate_tournament_win_loss_averages(participant_id):
            # Get all throws for this participant in this tournament
            cursor.execute("""
                SELECT t.score, t.remaining_score, t.darts_used, t.side_number, t.round_number,
                       l.leg_number, l.winner_side, l.cup_match_id
                FROM throws t
                JOIN legs l ON t.leg_id = l.id
                JOIN cup_matches cm ON l.cup_match_id = cm.id
                WHERE cm.tournament_id = ? 
                AND (
                    (t.side_number = 1 AND cm.participant1_id = ?) OR
                    (t.side_number = 2 AND cm.participant2_id = ?)
                )
                ORDER BY l.id, t.round_number
            """, (tid, participant_id, participant_id))
            
            all_throws = cursor.fetchall()
            if not all_throws:
                return 0, 0  # won_avg, lost_avg
            
            # Group throws by leg and determine win/loss
            won_legs_throws = []
            lost_legs_throws = []
            
            current_leg_throws = []
            current_leg_id = None
            current_side_number = None
            current_winner_side = None
            
            for throw in all_throws:
                leg_id = (throw[5], throw[7])  # leg_number, cup_match_id as unique identifier
                
                if leg_id != current_leg_id:
                    # Process previous leg if exists
                    if current_leg_throws:
                        if current_winner_side == current_side_number:
                            won_legs_throws.extend(current_leg_throws)
                        else:
                            lost_legs_throws.extend(current_leg_throws)
                    
                    # Start new leg
                    current_leg_throws = []
                    current_leg_id = leg_id
                    current_side_number = throw[3]  # side_number
                    current_winner_side = throw[6]  # winner_side
                
                # Add throw data matching goldenstat format
                throw_data = {
                    'score': throw[0],
                    'remaining_score': throw[1], 
                    'darts_used': throw[2] if throw[2] is not None else 3,
                    'round_number': throw[4]
                }
                current_leg_throws.append(throw_data)
            
            # Process last leg
            if current_leg_throws:
                if current_winner_side == current_side_number:
                    won_legs_throws.extend(current_leg_throws)
                else:
                    lost_legs_throws.extend(current_leg_throws)
            
            # Calculate averages using same logic as series matches
            def calculate_total_score_from_throws(throws):
                if not throws:
                    return 0
                    
                # Group by leg (using round pattern to detect leg boundaries)
                legs = []
                current_leg = []
                
                for throw in throws:
                    current_leg.append(throw)
                    # New leg starts when round_number resets to lower value
                    if len(current_leg) > 1 and current_leg[-1]['round_number'] <= current_leg[-2]['round_number']:
                        legs.append(current_leg[:-1])  # Previous leg complete
                        current_leg = [current_leg[-1]]  # Start new leg
                
                if current_leg:
                    legs.append(current_leg)
                
                total_score = 0
                for leg_throws in legs:
                    # Sort by round_number to ensure proper order
                    leg_throws.sort(key=lambda x: x['round_number'])
                    
                    for i, throw in enumerate(leg_throws):
                        if throw['remaining_score'] == 0 and i > 0:
                            # Checkout via remaining_score = 0, calculate from previous
                            prev_remaining = leg_throws[i-1]['remaining_score']
                            total_score += prev_remaining
                        else:
                            # Regular throw
                            total_score += throw['score']
                
                return total_score

            def calculate_total_darts_from_throws(throws):
                return sum(throw['darts_used'] for throw in throws)

            won_total_score = calculate_total_score_from_throws(won_legs_throws)
            won_total_darts = calculate_total_darts_from_throws(won_legs_throws)
            
            lost_total_score = calculate_total_score_from_throws(lost_legs_throws)
            lost_total_darts = calculate_total_darts_from_throws(lost_legs_throws)
            
            won_avg = (won_total_score * 3 / won_total_darts) if won_total_darts > 0 else 0
            lost_avg = (lost_total_score * 3 / lost_total_darts) if lost_total_darts > 0 else 0
            
            return won_avg, lost_avg

        # Add win/loss averages and match statistics to each participant
        for participant in participants:
            won_avg, lost_avg = calculate_tournament_win_loss_averages(participant['id'])
            participant['won_legs_avg'] = round(won_avg, 2)
            participant['lost_legs_avg'] = round(lost_avg, 2)
            
            # Calculate won/lost matches count (group by opponent to avoid duplicates)
            cursor.execute("""
                SELECT 
                    COUNT(DISTINCT opponent_id) as total_matches,
                    SUM(CASE WHEN wins > losses THEN 1 ELSE 0 END) as won_matches
                FROM (
                    SELECT 
                        CASE WHEN cm.participant1_id = ? THEN cm.participant2_id ELSE cm.participant1_id END as opponent_id,
                        SUM(CASE WHEN (cm.participant1_id = ? AND cm.p1_legs_won > cm.p2_legs_won) OR 
                                      (cm.participant2_id = ? AND cm.p2_legs_won > cm.p1_legs_won) 
                            THEN 1 ELSE 0 END) as wins,
                        SUM(CASE WHEN (cm.participant1_id = ? AND cm.p1_legs_won < cm.p2_legs_won) OR 
                                      (cm.participant2_id = ? AND cm.p2_legs_won < cm.p1_legs_won) 
                            THEN 1 ELSE 0 END) as losses
                    FROM cup_matches cm 
                    WHERE cm.tournament_id = ? 
                    AND (cm.participant1_id = ? OR cm.participant2_id = ?)
                    AND cm.p1_legs_won IS NOT NULL AND cm.p2_legs_won IS NOT NULL
                    GROUP BY opponent_id
                )
            """, (participant['id'], participant['id'], participant['id'], participant['id'], participant['id'], tid, participant['id'], participant['id']))
            
            match_stats = cursor.fetchone()
            if match_stats:
                total_matches = match_stats[0] or 0
                won_matches = match_stats[1] or 0
                lost_matches = total_matches - won_matches
                
                participant['won_matches'] = won_matches
                participant['lost_matches'] = lost_matches 
                participant['total_matches'] = total_matches
            else:
                participant['won_matches'] = 0
                participant['lost_matches'] = 0
                participant['total_matches'] = 0

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

        # Calculate win/loss leg averages for both participants
        def calculate_match_win_loss_averages(participant_id, side_number):
            # Get all throws for this participant in this specific match
            cursor.execute("""
                SELECT t.score, t.remaining_score, t.darts_used, t.round_number,
                       l.leg_number, l.winner_side
                FROM throws t
                JOIN legs l ON t.leg_id = l.id
                WHERE l.cup_match_id = ? AND t.side_number = ?
                ORDER BY l.leg_number, t.round_number
            """, (mid, side_number))
            
            all_throws = cursor.fetchall()
            if not all_throws:
                return 0, 0, 0, 0  # won_avg, lost_avg, won_legs_count, lost_legs_count
            
            # Group throws by leg and determine win/loss
            won_legs_throws = []
            lost_legs_throws = []
            won_legs_count = 0
            lost_legs_count = 0
            
            current_leg_throws = []
            current_leg_number = None
            current_winner_side = None
            
            for throw in all_throws:
                leg_number = throw[4]  # leg_number
                winner_side = throw[5]  # winner_side
                
                if leg_number != current_leg_number:
                    # Process previous leg if exists
                    if current_leg_throws:
                        if current_winner_side == side_number:
                            won_legs_throws.extend(current_leg_throws)
                            won_legs_count += 1
                        else:
                            lost_legs_throws.extend(current_leg_throws)
                            lost_legs_count += 1
                    
                    # Start new leg
                    current_leg_throws = []
                    current_leg_number = leg_number
                    current_winner_side = winner_side
                
                # Add throw data
                throw_data = {
                    'score': throw[0],
                    'remaining_score': throw[1],
                    'darts_used': throw[2] if throw[2] is not None else 3,
                    'round_number': throw[3]
                }
                current_leg_throws.append(throw_data)
            
            # Process last leg
            if current_leg_throws:
                if current_winner_side == side_number:
                    won_legs_throws.extend(current_leg_throws)
                    won_legs_count += 1
                else:
                    lost_legs_throws.extend(current_leg_throws)
                    lost_legs_count += 1
            
            # Calculate averages using same logic as series matches
            def calculate_total_score_from_match_throws(throws):
                if not throws:
                    return 0
                    
                total_score = 0
                current_leg_throws = []
                
                for throw in throws:
                    current_leg_throws.append(throw)
                    # Detect leg boundaries by checking if round_number decreased
                    if len(current_leg_throws) > 1 and current_leg_throws[-1]['round_number'] < current_leg_throws[-2]['round_number']:
                        # Process previous leg (all throws except the last one)
                        leg_throws = current_leg_throws[:-1]
                        leg_throws.sort(key=lambda x: x['round_number'])
                        
                        for i, leg_throw in enumerate(leg_throws):
                            if leg_throw['remaining_score'] == 0 and i > 0:
                                # Checkout - calculate from previous remaining_score
                                prev_remaining = leg_throws[i-1]['remaining_score']
                                total_score += prev_remaining
                            else:
                                # Regular throw
                                total_score += leg_throw['score']
                        
                        # Start new leg with current throw
                        current_leg_throws = [current_leg_throws[-1]]
                
                # Process final leg
                if current_leg_throws:
                    current_leg_throws.sort(key=lambda x: x['round_number'])
                    for i, throw in enumerate(current_leg_throws):
                        if throw['remaining_score'] == 0 and i > 0:
                            prev_remaining = current_leg_throws[i-1]['remaining_score']
                            total_score += prev_remaining
                        else:
                            total_score += throw['score']
                
                return total_score

            def calculate_total_darts_from_throws(throws):
                return sum(throw['darts_used'] for throw in throws)

            won_total_score = calculate_total_score_from_match_throws(won_legs_throws)
            won_total_darts = calculate_total_darts_from_throws(won_legs_throws)
            
            lost_total_score = calculate_total_score_from_match_throws(lost_legs_throws)
            lost_total_darts = calculate_total_darts_from_throws(lost_legs_throws)
            
            won_avg = (won_total_score * 3 / won_total_darts) if won_total_darts > 0 else 0
            lost_avg = (lost_total_score * 3 / lost_total_darts) if lost_total_darts > 0 else 0
            
            return won_avg, lost_avg, won_legs_count, lost_legs_count

        # Calculate for both participants
        p1_won_avg, p1_lost_avg, p1_won_legs, p1_lost_legs = calculate_match_win_loss_averages(match['participant1_id'], 1)
        p2_won_avg, p2_lost_avg, p2_won_legs, p2_lost_legs = calculate_match_win_loss_averages(match['participant2_id'], 2)

        # Add win/loss data to match info
        match['p1_won_legs_avg'] = round(p1_won_avg, 2)
        match['p1_lost_legs_avg'] = round(p1_lost_avg, 2)
        match['p1_won_legs_count'] = p1_won_legs
        match['p1_lost_legs_count'] = p1_lost_legs
        
        match['p2_won_legs_avg'] = round(p2_won_avg, 2)
        match['p2_lost_legs_avg'] = round(p2_lost_avg, 2)
        match['p2_won_legs_count'] = p2_won_legs
        match['p2_lost_legs_count'] = p2_lost_legs

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

        # Find player IDs: the canonical player + any aliases mapped to them
        cursor.execute("""
            SELECT id FROM players WHERE name = ?
            UNION
            SELECT alias_player_id FROM cup_player_mappings cpm
            JOIN players pl ON pl.id = cpm.canonical_player_id
            WHERE pl.name = ?
        """, (player_name, player_name))
        player_ids = [row[0] for row in cursor.fetchall()]

        if not player_ids:
            conn.close()
            return jsonify({'player_name': player_name, 'matches': [], 'fun_facts': []})

        placeholders = ','.join('?' * len(player_ids))

        # Find all matches where this player participated (either side)
        # Uses player IDs to include matches from alias players
        cursor.execute(f"""
            SELECT cm.id, cm.phase, cm.phase_detail,
                   cm.p1_legs_won, cm.p2_legs_won,
                   cm.p1_average, cm.p2_average,
                   cm.has_detail,
                   cm.participant1_id, cm.participant2_id,
                   COALESCE(
                       (SELECT GROUP_CONCAT(
                           COALESCE(cpm.canonical_name, pl.name), ' & ')
                        FROM participant_players pp
                        JOIN players pl ON pp.player_id = pl.id
                        LEFT JOIN cup_player_mappings cpm ON cpm.alias_player_id = pl.id
                        WHERE pp.participant_id = p1.id), p1.name) as p1_name,
                   COALESCE(
                       (SELECT GROUP_CONCAT(
                           COALESCE(cpm.canonical_name, pl.name), ' & ')
                        FROM participant_players pp
                        JOIN players pl ON pp.player_id = pl.id
                        LEFT JOIN cup_player_mappings cpm ON cpm.alias_player_id = pl.id
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
                WHERE pp.player_id IN ({placeholders})
            ) OR cm.participant2_id IN (
                SELECT pp.participant_id FROM participant_players pp
                WHERE pp.player_id IN ({placeholders})
            )
            ORDER BY t.tournament_date DESC, cm.phase, cm.phase_detail, cm.id
        """, player_ids + player_ids)
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
