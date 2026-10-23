"""Tests for player routes (/api/players, /api/player/<name>, etc.)"""
import sqlite3
import os


def _get_sample_player(test_db_dir):
    """Get a real player name from the test database."""
    db = os.path.join(test_db_dir, "goldenstat.db")
    conn = sqlite3.connect(db)
    row = conn.execute("SELECT name FROM players LIMIT 1").fetchone()
    conn.close()
    return row[0] if row else None


class TestPlayerSearch:
    def test_players_search_returns_json(self, client):
        resp = client.get("/api/players?search=a")
        assert resp.status_code == 200
        data = resp.get_json()
        assert isinstance(data, (list, dict))

    def test_players_empty_search(self, client):
        resp = client.get("/api/players")
        assert resp.status_code == 200


class TestPlayerDetail:
    def test_player_returns_json(self, client, test_db_dir):
        player = _get_sample_player(test_db_dir)
        if player is None:
            return  # skip if no data
        resp = client.get(f"/api/player/{player}")
        assert resp.status_code == 200
        data = resp.get_json()
        assert isinstance(data, dict)

    def test_player_not_found(self, client):
        resp = client.get("/api/player/NonExistentPlayer12345")
        assert resp.status_code in (200, 404)

    def test_player_detailed(self, client, test_db_dir):
        player = _get_sample_player(test_db_dir)
        if player is None:
            return
        resp = client.get(f"/api/player/{player}/detailed")
        assert resp.status_code == 200
        data = resp.get_json()
        assert isinstance(data, dict)



class TestPlayerThrows:
    def test_player_throws(self, client, test_db_dir):
        player = _get_sample_player(test_db_dir)
        if player is None:
            return
        resp = client.get(f"/api/player/{player}/throws")
        assert resp.status_code == 200
        data = resp.get_json()
        assert isinstance(data, (list, dict))
