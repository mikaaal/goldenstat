"""Tests for match routes (/api/sub_match, /api/match, etc.)"""
import sqlite3
import os


def _get_sample_ids(test_db_dir):
    """Get a real match_id and sub_match_id from the test database."""
    db = os.path.join(test_db_dir, "goldenstat.db")
    conn = sqlite3.connect(db)
    match_row = conn.execute("SELECT id FROM matches LIMIT 1").fetchone()
    sub_row = conn.execute("SELECT id FROM sub_matches LIMIT 1").fetchone()
    conn.close()
    return (
        match_row[0] if match_row else None,
        sub_row[0] if sub_row else None,
    )


class TestSubMatch:
    def test_sub_match_returns_json(self, client, test_db_dir):
        match_id, sub_match_id = _get_sample_ids(test_db_dir)
        if sub_match_id is None:
            return
        resp = client.get(f"/api/sub_match/{sub_match_id}")
        assert resp.status_code == 200
        data = resp.get_json()
        assert isinstance(data, dict)

    def test_sub_match_not_found(self, client):
        resp = client.get("/api/sub_match/999999")
        assert resp.status_code in (200, 404)

    def test_sub_match_match_id(self, client, test_db_dir):
        _, sub_match_id = _get_sample_ids(test_db_dir)
        if sub_match_id is None:
            return
        resp = client.get(f"/api/sub_match/{sub_match_id}/match_id")
        assert resp.status_code == 200


class TestMatchLegs:
    def test_match_legs_returns_json(self, client, test_db_dir):
        match_id, _ = _get_sample_ids(test_db_dir)
        if match_id is None:
            return
        resp = client.get(f"/api/match/{match_id}/legs")
        assert resp.status_code == 200
        data = resp.get_json()
        assert isinstance(data, (list, dict))


class TestMatchOverview:
    def test_match_overview_returns_json(self, client, test_db_dir):
        match_id, _ = _get_sample_ids(test_db_dir)
        if match_id is None:
            return
        resp = client.get(f"/api/match/{match_id}/overview")
        assert resp.status_code == 200
        data = resp.get_json()
        assert isinstance(data, dict)


class TestSeriesMatches:
    def test_series_matches_returns_json(self, client):
        resp = client.get("/api/series_matches")
        assert resp.status_code == 200
        data = resp.get_json()
        assert isinstance(data, (list, dict))


class TestMatchPages:
    def test_match_overview_page(self, client):
        resp = client.get("/match_overview")
        assert resp.status_code == 200

    def test_sub_match_throws_page(self, client):
        resp = client.get("/sub_match_throws")
        assert resp.status_code == 200

    def test_series_matches_page(self, client):
        resp = client.get("/series_matches")
        assert resp.status_code == 200
