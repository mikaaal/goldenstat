"""Tests for league routes (/, /api/divisions, /api/top-stats, etc.)"""


class TestIndex:
    def test_index_returns_html(self, client):
        resp = client.get("/")
        assert resp.status_code == 200
        assert b"html" in resp.data.lower()

    def test_index_with_league_param(self, client):
        resp = client.get("/?league=riksserien")
        assert resp.status_code == 200


class TestDivisions:
    def test_divisions_returns_json(self, client):
        resp = client.get("/api/divisions")
        assert resp.status_code == 200
        data = resp.get_json()
        assert isinstance(data, (list, dict))

    def test_divisions_riksserien(self, client):
        resp = client.get("/api/divisions?league=riksserien")
        assert resp.status_code == 200


class TestLeagues:
    def test_leagues_returns_json(self, client):
        resp = client.get("/api/leagues")
        assert resp.status_code == 200
        data = resp.get_json()
        assert isinstance(data, (list, dict))


class TestOverview:
    def test_overview_returns_json(self, client):
        resp = client.get("/api/overview")
        assert resp.status_code == 200
        data = resp.get_json()
        assert isinstance(data, (list, dict))


class TestTopStats:
    def test_top_stats_returns_json(self, client):
        resp = client.get("/api/top-stats")
        assert resp.status_code == 200
        data = resp.get_json()
        assert isinstance(data, (list, dict))

    def test_top_stats_with_division(self, client):
        resp = client.get("/api/top-stats?division=Division+1")
        assert resp.status_code == 200


class TestWeeklyStats:
    def test_weekly_stats_returns_json(self, client):
        resp = client.get("/api/weekly-stats")
        assert resp.status_code == 200
        data = resp.get_json()
        assert isinstance(data, (list, dict))


class TestFiltersAreParameterized:
    INJECTION = "x' OR '1'='1"

    def test_season_is_not_interpolated(self, client):
        resp = client.get("/api/top-stats", query_string={"season": self.INJECTION})
        assert resp.status_code == 200
        assert resp.get_json()["top_averages"] == []

    def test_division_is_not_interpolated(self, client):
        resp = client.get("/api/weekly-stats", query_string={
            "date_start": "2000-01-01", "date_end": "2100-01-01", "division": self.INJECTION})
        assert resp.status_code == 200
        assert resp.get_json()["total_matches"] == 0


class TestCacheKey:
    def _key(self, app, url, *params):
        from routes.league import _cache_key
        with app.test_request_context(url):
            return _cache_key("top_stats", *params)

    def test_unknown_params_do_not_change_key(self, app):
        assert self._key(app, "/api/top-stats?season=2025/2026&x=1", "season") == \
            self._key(app, "/api/top-stats?season=2025/2026", "season")

    def test_unknown_league_uses_default_key(self, app):
        assert self._key(app, "/api/top-stats?league=foo") == self._key(app, "/api/top-stats")

    def test_known_league_gets_own_key(self, app):
        assert self._key(app, "/api/top-stats?league=riksserien") != self._key(app, "/api/top-stats")


class TestAvailableWeeks:
    def test_available_weeks_returns_json(self, client):
        resp = client.get("/api/available-weeks")
        assert resp.status_code == 200
        data = resp.get_json()
        assert isinstance(data, (list, dict))


class TestLastImport:
    def test_last_import_returns_json(self, client):
        resp = client.get("/api/last-import")
        # 404 is expected when no import logs exist in the test environment
        assert resp.status_code in (200, 404)
        data = resp.get_json()
        assert isinstance(data, dict)


class TestTeamsList:
    def test_teams_returns_json(self, client):
        resp = client.get("/api/teams")
        assert resp.status_code == 200
        data = resp.get_json()
        assert isinstance(data, (list, dict))
