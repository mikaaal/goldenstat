"""Tests for the title searches in the nightly cup import."""
import re
from datetime import datetime
from unittest.mock import MagicMock, patch

import nightly_cup_import as nci


def _search(name):
    return next(s for s in nci.SEARCHES if s["name"] == name)


def _matches(name, title):
    return bool(re.search(_search(name)["pattern"], title, re.IGNORECASE))


class TestPatterns:
    def test_club_cups_match(self):
        assert _matches("Goldtown", "Goldtown onsdagscup 21/10")
        assert _matches("Ludvika", "Ludvika Tisdagscup omg 8")
        assert _matches("Oilers", "Oilers poängsamling 5/4-24")
        assert _matches("BDC", "BDC KM 2026 DS")
        assert _matches("SSDC Closed", "SSDC Closed 20261030 - Öppensingel")

    def test_league_matches_against_club_do_not_match(self):
        assert not _matches("Oilers", "Oilers A - East B")
        assert not _matches("East", "EAST -SSDC")

    def test_test_events_do_not_match(self):
        assert not _matches("Goldtown", "Goldtown Test cup")
        assert not _matches("SSDC Closed", "SSDC TESTClosed 20251031 - Öppendubbel")

    def test_foreign_namesakes_do_not_match(self):
        assert not _matches("TDC", "TDC Friday Darts Cup")
        assert not _matches("TDC", "TDC Off Season Cup")
        assert not _matches("East", "ADG Challenge Cup - East&North Africa")

    def test_word_boundaries(self):
        assert not _matches("TDC", "StDC lördagscup")
        assert not _matches("NDK", "Sundkvist cup")


def _ts(day):
    return int(datetime.fromisoformat(day).timestamp())


def _t(tdid, title, day, darts=5000, t_date=True):
    t = {"tdid": tdid, "title": title, "createTime": _ts(day), "d": darts}
    t["t_date"] = _ts(day) if t_date else 0
    return t


def _pages(*pages):
    responses = []
    for page in pages:
        r = MagicMock()
        r.json.return_value = page
        responses.append(r)
    return responses


SINCE = datetime(2023, 11, 1)
SEARCH = {"name": "Goldtown", "keyword": "goldtown", "pattern": nci._club("goldtown")}


@patch("nightly_cup_import.time.sleep")
@patch("nightly_cup_import.requests.post")
class TestSearchTournaments:
    def test_filters_title_darts_and_date(self, post, _sleep):
        post.side_effect = _pages([
            _t("t_a", "Goldtown onsdagscup", "2026-10-21"),
            _t("t_b", "Goldtown A - Oilers B", "2026-10-20"),
            _t("t_c", "Goldtown fredagscup", "2026-10-17", darts=0),
            _t("t_d", "Goldtown lördagscup", "2023-01-01"),
        ])
        found = nci.search_tournaments(SEARCH, SINCE)
        assert [t["tdid"] for t in found] == ["t_a"]

    def test_pages_until_since(self, post, _sleep):
        full = [_t(f"t_{i}", "Goldtown cup", "2026-01-01") for i in range(20)]
        post.side_effect = _pages(full, [_t("t_old", "Goldtown cup", "2022-01-01")])
        found = nci.search_tournaments(SEARCH, SINCE)
        assert len(found) == 20
        assert post.call_count == 2
        assert post.call_args_list[1].args[0].endswith("skip=20&count=20")

    def test_missing_t_date_falls_back_to_create_time(self, post, _sleep):
        post.side_effect = _pages([_t("t_a", "Goldtown cup", "2026-10-21", t_date=False)])
        found = nci.search_tournaments(SEARCH, SINCE)
        assert found[0]["t_date"] == _ts("2026-10-21")


class TestBacklog:
    def test_saved_tournaments_are_loaded_until_imported(self, tmp_path):
        db = str(tmp_path / "cups.db")
        conn = nci.sqlite3.connect(db)
        conn.execute("CREATE TABLE tournaments (tdid VARCHAR(50))")
        conn.commit()
        conn.close()

        nci.save_backlog([
            {"tdid": "t_a", "title": "Goldtown cup", "t_date": 2, "league": "Goldtown"},
            {"tdid": "t_b", "title": "Ludvika cup", "t_date": 1, "league": "Ludvika"},
        ], db)
        assert {t["tdid"] for t in nci.load_backlog(db)} == {"t_a", "t_b"}

        conn = nci.sqlite3.connect(db)
        conn.execute("INSERT INTO tournaments VALUES ('t_a')")
        conn.commit()
        conn.close()
        assert [t["tdid"] for t in nci.load_backlog(db)] == ["t_b"]

    def test_saving_twice_keeps_one_row(self, tmp_path):
        db = str(tmp_path / "cups.db")
        conn = nci.sqlite3.connect(db)
        conn.execute("CREATE TABLE tournaments (tdid VARCHAR(50))")
        conn.commit()
        conn.close()
        t = {"tdid": "t_a", "title": "Goldtown cup", "t_date": 2, "league": "Goldtown"}
        nci.save_backlog([t], db)
        nci.save_backlog([t], db)
        assert len(nci.load_backlog(db)) == 1


class TestDates:
    def test_t_date_is_used_when_set(self):
        assert nci.tournament_date_from({"t_date": _ts("2026-10-30"), "createTime": 1}) \
            == "2026-10-30T00:00:00"

    def test_missing_t_date_falls_back_to_start_time(self):
        data = {"t_date": 0, "s_date": _ts("2026-10-30"), "createTime": _ts("2026-10-29")}
        assert nci.tournament_date_from(data) == "2026-10-30T00:00:00"
        assert nci.tournament_date_from({"t_date": 0, "createTime": _ts("2026-10-29")}) \
            == "2026-10-29T00:00:00"

    def test_no_time_at_all_gives_none(self):
        assert nci.tournament_date_from({"t_date": 0}) is None

    @patch("nightly_cup_import.time.sleep")
    @patch("nightly_cup_import.CupImporter")
    def test_undated_tournaments_get_a_date(self, importer, _sleep, tmp_path):
        db = str(tmp_path / "cups.db")
        conn = nci.sqlite3.connect(db)
        conn.execute("CREATE TABLE tournaments (tdid VARCHAR(50), tournament_date TIMESTAMP)")
        conn.execute("INSERT INTO tournaments VALUES ('t_a', NULL), ('t_b', '2025-01-01')")
        conn.commit()
        conn.close()
        importer.return_value.fetch_tournament_data.return_value = \
            {"t_date": 0, "s_date": _ts("2026-10-30")}

        nci.fill_missing_dates(db)

        importer.return_value.fetch_tournament_data.assert_called_once_with("t_a")
        conn = nci.sqlite3.connect(db)
        rows = dict(conn.execute("SELECT tdid, tournament_date FROM tournaments"))
        conn.close()
        assert rows == {"t_a": "2026-10-30T00:00:00", "t_b": "2025-01-01"}


def _entries(names):
    return [{"tpid": f"tp{i}", "name": n} for i, n in enumerate(names)]


class TestMinPlayers:
    def _importer(self, entry_list):
        importer = nci.CupImporter.__new__(nci.CupImporter)
        importer.db = MagicMock()
        importer.fetch_tournament_data = MagicMock(
            return_value={"title": "Liten cup", "entry_list": entry_list})
        return importer

    def test_small_singles_cup_is_skipped_before_anything_is_written(self):
        importer = self._importer(_entries([f"Spelare {i}" for i in range(11)]))
        assert importer.import_tournament("t_a", min_players=12) is False
        importer.db.get_or_create_tournament.assert_not_called()

    def test_doubles_count_both_players(self):
        # 6 pairs is 12 players, which is enough
        importer = self._importer(_entries([f"A{i} & B{i}" for i in range(6)]))
        importer.db.get_or_create_tournament.side_effect = RuntimeError("past the check")
        try:
            importer.import_tournament("t_a", min_players=12)
        except RuntimeError as e:
            assert str(e) == "past the check"
        else:
            raise AssertionError("cup with 12 players was skipped")

    def test_skipped_cups_count_as_existing_and_leave_the_backlog(self, tmp_path):
        db = str(tmp_path / "cups.db")
        conn = nci.sqlite3.connect(db)
        conn.execute("CREATE TABLE tournaments (tdid VARCHAR(50))")
        conn.commit()
        conn.close()
        nci.save_backlog([{"tdid": "t_a", "title": "Liten cup", "t_date": 1, "league": "X"}], db)

        nci.save_skipped("t_a", "Liten cup", db)

        assert nci.get_existing_tdids(db) == {"t_a"}
        assert nci.load_backlog(db) == []
