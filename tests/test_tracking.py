"""Tests for tracking/analytics routes."""
import json


class TestTrackTab:
    def test_track_tab(self, client):
        resp = client.post(
            "/api/track-tab",
            data=json.dumps({"tab": "players"}),
            content_type="application/json",
        )
        assert resp.status_code == 200
        assert resp.get_json()["status"] == "ok"


class TestTrackClick:
    def test_track_click(self, client):
        resp = client.post(
            "/api/track-click",
            data=json.dumps({"event": "test_click"}),
            content_type="application/json",
        )
        assert resp.status_code == 200
        assert resp.get_json()["status"] == "ok"


class TestTrackPageview:
    def test_track_pageview(self, client):
        resp = client.post(
            "/api/track-pageview",
            data=json.dumps({"page": "index"}),
            content_type="application/json",
        )
        assert resp.status_code == 200
        assert resp.get_json()["status"] == "ok"


class TestTrackSearch:
    def test_track_search(self, client):
        resp = client.post(
            "/api/track-search",
            data=json.dumps({"query": "test"}),
            content_type="application/json",
        )
        assert resp.status_code == 200
        assert resp.get_json()["status"] == "ok"
