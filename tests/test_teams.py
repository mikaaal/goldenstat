"""Tests for team routes (/api/team/<name>/lineup, /api/team/<name>/players, etc.)"""
import sqlite3
import os


def _get_sample_team(test_db_dir):
    """Get a real team name from the test database."""
    db = os.path.join(test_db_dir, "goldenstat.db")
    conn = sqlite3.connect(db)
    row = conn.execute("SELECT name FROM teams LIMIT 1").fetchone()
    conn.close()
    return row[0] if row else None


class TestTeamLineup:
    def test_team_lineup_returns_json(self, client, test_db_dir):
        team = _get_sample_team(test_db_dir)
        if team is None:
            return
        resp = client.get(f"/api/team/{team}/lineup")
        assert resp.status_code == 200
        data = resp.get_json()
        assert isinstance(data, (list, dict))


class TestTeamPlayers:
    def test_team_players_returns_json(self, client, test_db_dir):
        team = _get_sample_team(test_db_dir)
        if team is None:
            return
        resp = client.get(f"/api/team/{team}/players")
        assert resp.status_code == 200
        data = resp.get_json()
        assert isinstance(data, (list, dict))


class TestTeamDoublesPairs:
    def test_doubles_pairs_returns_json(self, client, test_db_dir):
        team = _get_sample_team(test_db_dir)
        if team is None:
            return
        resp = client.get(f"/api/team/{team}/doubles-pairs")
        assert resp.status_code == 200
        data = resp.get_json()
        assert isinstance(data, (list, dict))


class TestClubPlayers:
    def test_club_players_returns_json(self, client, test_db_dir):
        team = _get_sample_team(test_db_dir)
        if team is None:
            return
        resp = client.get(f"/api/club/{team}/players")
        assert resp.status_code == 200
        data = resp.get_json()
        assert isinstance(data, (list, dict))
