"""Tests for singles/doubles detection.

Divisions name their sub-matches differently: "Doubles1" in most divisions,
"Dubbel 1 (Borta)" in SL6 and 1FA from the 2026/2027 season.
"""
import pytest

from new_season_importer import detect_match_type


def _stats(team_sizes):
    return [{"order": [{"oname": f"Spelare {i}"} for i in range(n)]} for n in team_sizes]


class TestDetectMatchType:
    @pytest.mark.parametrize("title", [
        "2A Division 2A Doubles1",
        "SL6 Division SL6 Dubbel 1 (Borta)",
        "1FA Division 1FA Dubbel 2 (Hemma)",
        "DS Damserien AD",
        "SL6 Division SL6 AD (Hemma)",
    ])
    def test_doubles_titles(self, title):
        assert detect_match_type(title, _stats([2, 2])) == "Doubles"

    @pytest.mark.parametrize("title", [
        "2A Division 2A Singles1",
        "SL6 Division SL6 Singel 5 (Hemma)",
        "1FA Division 1FA Singel2 (Borta)",
    ])
    def test_singles_titles(self, title):
        assert detect_match_type(title, _stats([1, 1])) == "Singles"

    def test_player_count_decides_when_title_is_silent(self):
        assert detect_match_type("Match 3", _stats([2, 2])) == "Doubles"
        assert detect_match_type("Match 3", _stats([1, 1])) == "Singles"

    def test_ad_without_registered_players(self):
        """AD is decided before the match, so the player list can be empty."""
        assert detect_match_type("SL6 Division SL6 AD (Hemma)", _stats([0, 0])) == "Doubles"

    def test_missing_title_and_stats(self):
        assert detect_match_type("", []) == "Singles"
        assert detect_match_type(None, None) == "Singles"

    def test_title_wins_over_player_count(self):
        """A doubles title stays doubles even if only one player was registered."""
        assert detect_match_type("SL6 Division SL6 Dubbel 1 (Borta)", _stats([1, 1])) == "Doubles"
