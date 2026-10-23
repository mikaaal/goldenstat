"""Tests for n01 URL helpers.

matches.match_url holds the tmid (older rows the full URL), while the URL
files hold full URLs with each fixture listed in both team orders.
"""
from n01_api import N01_HOST, match_url, mirrored_tmid, tmid_from_url

TMID = "t_rTdF_8606_lg_0_cjve_8WQj_MCPO"


class TestTmidFromUrl:
    def test_current_host(self):
        assert tmid_from_url(match_url(TMID)) == TMID

    def test_old_host(self):
        old = ("https://tk2-228-23746.vs.sakura.ne.jp/n01/tournament/"
               f"n01_online_t.php?cmd=get_setdata&tmid={TMID}")
        assert tmid_from_url(old) == TMID

    def test_bare_tmid_unchanged(self):
        assert tmid_from_url(TMID) == TMID


class TestMirroredTmid:
    def test_swaps_teams(self):
        assert mirrored_tmid(TMID) == "t_rTdF_8606_lg_0_cjve_MCPO_8WQj"

    def test_round_trip(self):
        assert mirrored_tmid(mirrored_tmid(TMID)) == TMID


def test_match_url_uses_host():
    assert match_url(TMID).startswith(f"https://{N01_HOST}/")
