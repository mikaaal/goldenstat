"""Tests for how the Riksserien import names its URL files and divisions."""
from pathlib import Path

import riksserien_daily_import as rdi
from riksserien_daily_import import RiksserienDailyImport


class TestDivisionCode:
    def test_named_divisions(self):
        assert RiksserienDailyImport.division_code("Elit") == "RSElit"
        assert RiksserienDailyImport.division_code("Elit Dam") == "RSElitDam"
        assert RiksserienDailyImport.division_code("Superettan") == "RSSup"

    def test_numbered_divisions(self):
        assert RiksserienDailyImport.division_code("Div 1A") == "RS1A"
        assert RiksserienDailyImport.division_code("Div 3I") == "RS3I"

    def test_unknown_title_still_gives_a_code(self):
        assert RiksserienDailyImport.division_code("Kval 2027") == "RSKval2027"


class TestParseFilename:
    def _parse(self, filename):
        # __init__ creates the log directory, which parsing a name does not need
        return object.__new__(RiksserienDailyImport).parse_filename(filename)

    def test_known_code(self):
        info = self._parse("t_817F_2404_match_urlsRSElit.txt")
        assert info["division_id"] == "t_817F_2404"
        assert info["division_name"] == "Elit"

    def test_division_not_in_the_map(self):
        assert self._parse("t_LhCN_0179_match_urlsRS3I.txt")["division_name"] == "Div 3I"
        assert self._parse("t_aGL7_5675_match_urlsRS2D.txt")["division_name"] == "Div 2D"

    def test_every_title_round_trips(self):
        for title in ["Elit", "Elit Dam", "Superettan", "Div 1B", "Div 2D", "Div 3I"]:
            filename = f"t_XXXX_0000_match_urls{RiksserienDailyImport.division_code(title)}.txt"
            assert self._parse(filename)["division_name"] == title


class TestRefreshUrlFiles:
    def test_files_are_written_per_division(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        monkeypatch.setattr(rdi, "URL_DIR", Path("riksserien_match_urls"))
        monkeypatch.setattr(rdi, "get_divisions", lambda lgid: [
            {"tdid": "t_817F_2404", "title": "Elit"},
            {"tdid": "t_LhCN_0179", "title": "Div 3I"},
        ])

        written = []

        class FakeGenerator:
            def save_urls_to_file(self, tdid, output_file):
                Path(output_file).write_text("x")
                written.append(Path(output_file).name)
                return True

        monkeypatch.setattr(rdi, "MatchUrlGenerator", FakeGenerator)
        RiksserienDailyImport().refresh_url_files()

        assert sorted(written) == ["t_817F_2404_match_urlsRSElit.txt", "t_LhCN_0179_match_urlsRS3I.txt"]

    def test_existing_files_are_kept_when_n01_fails(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        monkeypatch.setattr(rdi, "URL_DIR", Path("riksserien_match_urls"))

        def fail(lgid):
            raise RuntimeError("timeout")

        monkeypatch.setattr(rdi, "get_divisions", fail)
        importer = RiksserienDailyImport()
        importer.refresh_url_files()

        assert any("timeout" in w for w in importer.import_log["warnings"])
