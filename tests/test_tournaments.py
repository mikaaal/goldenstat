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
