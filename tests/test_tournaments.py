"""Tests for tournament routes (/api/tournaments, etc.)"""
import sqlite3
import os


def _get_sample_tournament(test_db_dir):
    """Get a real tournament id from the cups database."""
    db = os.path.join(test_db_dir, "cups.db")
    if not os.path.exists(db):
        return None, None
    conn = sqlite3.connect(db)
    row = conn.execute("SELECT id FROM tournaments LIMIT 1").fetchone()
    match_row = conn.execute(
        "SELECT id FROM cup_matches LIMIT 1"
    ).fetchone()
    conn.close()
    return (
        row[0] if row else None,
        match_row[0] if match_row else None,
    )


def _get_sample_cup_player(test_db_dir):
    """Get a real player name from cups database."""
    db = os.path.join(test_db_dir, "cups.db")
    if not os.path.exists(db):
        return None
    conn = sqlite3.connect(db)
    row = conn.execute("SELECT name FROM players LIMIT 1").fetchone()
    conn.close()
    return row[0] if row else None


class TestTournamentsList:
    def test_tournaments_returns_json(self, client):
        resp = client.get("/api/tournaments")
        assert resp.status_code == 200
        data = resp.get_json()
        assert isinstance(data, (list, dict))


class TestTournamentDetail:
    def test_tournament_detail(self, client, test_db_dir):
        tid, _ = _get_sample_tournament(test_db_dir)
        if tid is None:
            return
        resp = client.get(f"/api/tournaments/{tid}")
        assert resp.status_code == 200
        data = resp.get_json()
        assert isinstance(data, dict)


class TestTournamentMatch:
    def test_tournament_match(self, client, test_db_dir):
        _, mid = _get_sample_tournament(test_db_dir)
        if mid is None:
            return
        resp = client.get(f"/api/tournaments/match/{mid}")
        assert resp.status_code == 200
        data = resp.get_json()
        assert isinstance(data, dict)


class TestTournamentPlayers:
    def test_tournament_players_list(self, client):
        resp = client.get("/api/tournaments/players")
        assert resp.status_code == 200
        data = resp.get_json()
        assert isinstance(data, (list, dict))

    def test_tournament_player_detail(self, client, test_db_dir):
        player = _get_sample_cup_player(test_db_dir)
        if player is None:
            return
        resp = client.get(f"/api/tournaments/player/{player}")
        assert resp.status_code == 200
        data = resp.get_json()
        assert isinstance(data, dict)


class TestCupTopStatsDisabled:
    def test_cup_top_stats_api_is_gone(self, client):
        assert client.get("/api/cup-top-stats").status_code == 404

    def test_cup_top_stats_page_is_gone(self, client):
        assert client.get("/tournaments/top").status_code == 404


class TestTournamentPages:
    def test_tournaments_page(self, client):
        resp = client.get("/tournaments")
        assert resp.status_code == 200

    def test_tournaments_list_page(self, client):
        resp = client.get("/tournaments/list")
        assert resp.status_code == 200

    def test_tournaments_players_page(self, client):
        resp = client.get("/tournaments/players")
        assert resp.status_code == 200


def _cup_match(match_id, p1, p2, date, tournament_id=1, p1_legs=3, p2_legs=1):
    return {
        "id": match_id, "p1_name": p1, "p2_name": p2,
        "p1_legs_won": p1_legs, "p2_legs_won": p2_legs,
        "p1_average": 50.0, "p2_average": 45.0,
        "tournament_id": tournament_id, "tournament_title": f"Cup {tournament_id}, extra",
        "tournament_date": date, "phase_label": "Poolspel",
    }


def _highest_checkout(facts):
    return next((f for f in facts if f["title"] == "Högsta utgång"), None)


class TestHighestCheckoutFact:
    def _facts(self, matches, checkouts):
        from routes.tournaments import calculate_fun_facts
        return calculate_fun_facts(matches, "Anna", checkouts)

    def test_uses_players_own_side(self):
        matches = [_cup_match(1, "Anna", "Bo", "2026-01-01"), _cup_match(2, "Cia", "Anna", "2026-02-01")]
        # Motståndarnas utgångar (sida 2 i match 1, sida 1 i match 2) ska inte räknas
        fact = _highest_checkout(self._facts(matches, {(1, 1): 81, (1, 2): 170, (2, 1): 160, (2, 2): 121}))
        assert fact["text"] == "121 mot Cia"
        assert fact["detail"] == "Cup 1 (2026-02-01)"
        assert fact["filter_tournaments"] == [1]

    def test_doubles_are_ignored(self):
        matches = [_cup_match(1, "Anna & Bo", "Cia & Dan", "2026-01-01"), _cup_match(2, "Anna", "Bo", "2026-02-01")]
        fact = _highest_checkout(self._facts(matches, {(1, 1): 150, (2, 1): 40}))
        assert fact["text"] == "40 mot Bo"

    def test_tie_shows_most_recent(self):
        matches = [_cup_match(1, "Anna", "Bo", "2026-03-01", tournament_id=2), _cup_match(2, "Anna", "Cia", "2026-01-01")]
        fact = _highest_checkout(self._facts(matches, {(1, 1): 100, (2, 1): 100}))
        assert fact["text"] == "100 mot Bo"

    def test_no_checkouts_no_fact(self):
        assert _highest_checkout(self._facts([_cup_match(1, "Anna", "Bo", "2026-01-01")], {})) is None


class TestPlayerCheckouts:
    def test_checkouts_are_valid_finishes(self, test_db_dir):
        from routes.tournaments import get_player_checkouts
        db = os.path.join(test_db_dir, "cups.db")
        if not os.path.exists(db):
            return
        conn = sqlite3.connect(db)
        player_id = conn.execute("""
            SELECT pp.player_id FROM participant_players pp
            JOIN cup_matches cm ON cm.participant1_id = pp.participant_id
            WHERE cm.has_detail = 1 LIMIT 1""").fetchone()
        if player_id is None:
            conn.close()
            return
        checkouts = get_player_checkouts(conn.cursor(), [player_id[0]])
        conn.close()
        assert checkouts
        assert all(2 <= v <= 170 and side in (1, 2) for (_, side), v in checkouts.items())
