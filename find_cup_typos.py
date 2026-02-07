"""
Find likely typo duplicates in cups.db player names.

Strategy: Split names into parts. At least one part must match exactly
(case-insensitive). The remaining parts must have edit distance <= 2.
This catches "Alexander Feldin" vs "Alexander Felldin" but NOT
"Peter" vs "Peder" or "Larry" vs "Carry".

Single-word names are excluded from fuzzy matching.
Already-mapped aliases (in cup_player_mappings) are excluded.

Output format is compatible with apply_cup_mappings.py.

Usage:
    python find_cup_typos.py              # Print proposed mappings for review
    python find_cup_typos.py --json       # Output as JSON
"""

import sqlite3
import json
import sys


def edit_distance(a, b):
    """Levenshtein edit distance."""
    if abs(len(a) - len(b)) > 2:
        return 99
    m, n = len(a), len(b)
    dp = list(range(n + 1))
    for i in range(1, m + 1):
        prev, dp[0] = dp[0], i
        for j in range(1, n + 1):
            temp = dp[j]
            dp[j] = min(dp[j] + 1, dp[j - 1] + 1, prev + (0 if a[i - 1] == b[j - 1] else 1))
            prev = temp
    return dp[n]


def split_name(name):
    """Split a name into lowercase parts."""
    return name.lower().split()


def is_fuzzy_match(parts_a, parts_b):
    """Check if two split names are a likely typo match.

    Strict rules to avoid false positives like Peter/Peder, Larry/Carry:
    - Both must have at least 2 parts
    - Must have the same number of parts
    - At least one part must match exactly
    - Differing parts: edit distance 1 only (max 2 for parts >= 10 chars)
    - Differing parts must start with the same character
    - Differing parts must be at least 4 chars long
    - Only one part may differ
    """
    if len(parts_a) < 2 or len(parts_b) < 2:
        return False
    if len(parts_a) != len(parts_b):
        return False

    exact_matches = 0
    diff_count = 0

    for pa, pb in zip(parts_a, parts_b):
        if pa == pb:
            exact_matches += 1
        else:
            diff_count += 1
            # Only one part may differ
            if diff_count > 1:
                return False
            # Must start with the same character
            if pa[0] != pb[0]:
                return False
            # Must be at least 4 chars
            if max(len(pa), len(pb)) < 4:
                return False
            d = edit_distance(pa, pb)
            # Strict: max edit distance 1, or 2 for long parts (>= 10 chars)
            max_dist = 2 if min(len(pa), len(pb)) >= 10 else 1
            if d > max_dist:
                return False

    return diff_count == 1 and exact_matches >= 1


def get_tournament_count(conn, player_id):
    """Count tournaments a player has participated in."""
    return conn.execute(
        "SELECT COUNT(*) FROM participant_players WHERE player_id = ?",
        (player_id,)
    ).fetchone()[0]


def find_typo_duplicates(db_path='cups.db'):
    conn = sqlite3.connect(db_path)

    # Get all player names, excluding already-mapped aliases
    rows = conn.execute("""
        SELECT id, name FROM players
        WHERE id NOT IN (SELECT alias_player_id FROM cup_player_mappings)
        ORDER BY id
    """).fetchall()

    players = [{'id': r[0], 'name': r[1]} for r in rows]

    # Pre-compute split names and tournament counts
    for p in players:
        p['parts'] = split_name(p['name'])
        p['count'] = get_tournament_count(conn, p['id'])

    # Group candidates by first-name to reduce O(n^2) comparisons
    from collections import defaultdict
    by_part = defaultdict(list)
    for p in players:
        for part in p['parts']:
            by_part[part].append(p)

    # Find matches
    seen_pairs = set()
    matches = []

    for part, group in by_part.items():
        for i in range(len(group)):
            for j in range(i + 1, len(group)):
                a, b = group[i], group[j]
                pair_key = (min(a['id'], b['id']), max(a['id'], b['id']))
                if pair_key in seen_pairs:
                    continue
                seen_pairs.add(pair_key)

                if is_fuzzy_match(a['parts'], b['parts']):
                    matches.append((a, b))

    # Build mappings: the one with more tournaments is canonical
    mappings = []
    canonical_decided = {}  # track to avoid conflicting mappings

    for a, b in matches:
        # Choose canonical: more tournaments wins, tie goes to lower id
        if a['count'] > b['count'] or (a['count'] == b['count'] and a['id'] < b['id']):
            canonical, alias = a, b
        else:
            canonical, alias = b, a

        # Skip if alias has already been assigned as canonical for another pair
        if alias['id'] in canonical_decided and canonical_decided[alias['id']] == 'canonical':
            continue

        mappings.append({
            'alias_player_id': alias['id'],
            'canonical_player_id': canonical['id'],
            'alias_name': alias['name'],
            'canonical_name': canonical['name'],
            'alias_count': alias['count'],
            'canonical_count': canonical['count'],
            'reason': 'typo',
        })

    conn.close()

    # Sort by canonical name for readability
    mappings.sort(key=lambda m: m['canonical_name'].lower())

    return mappings


def main():
    output_json = '--json' in sys.argv
    db_path = 'cups.db'

    mappings = find_typo_duplicates(db_path)

    if output_json:
        # Strip count fields for apply_cup_mappings compatibility
        for m in mappings:
            m.pop('alias_count', None)
            m.pop('canonical_count', None)
        print(json.dumps(mappings, ensure_ascii=False, indent=2))
        return

    print(f"Found {len(mappings)} likely typo mappings\n")
    print(f"{'Alias':<45} -> {'Canonical':<45} {'alias':>5} {'canon':>5}")
    print('-' * 110)

    for m in mappings:
        print(f"{m['alias_name']:<45} -> {m['canonical_name']:<45} {m['alias_count']:>5} {m['canonical_count']:>5}")

    print(f"\nTotal: {len(mappings)} proposed mappings")


if __name__ == '__main__':
    main()
