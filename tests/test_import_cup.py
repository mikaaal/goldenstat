"""Tests for import_cup leg handling."""
from import_cup import CupImporter

START = {'score': 0, 'left': 501}


class TestIsUnplayedLeg:
    def test_unplayed_trailing_leg(self):
        leg = {'endFlag': 0, 'currentRound': 0, 'winner': 0,
               'playerData': [[START], [START]]}
        assert CupImporter._is_unplayed_leg(leg)

    def test_finished_leg(self):
        leg = {'endFlag': 1, 'winner': 1,
               'playerData': [[START, {'score': 100, 'left': 401}],
                              [START, {'score': -3, 'left': 0}]]}
        assert not CupImporter._is_unplayed_leg(leg)

    def test_finished_leg_without_throws_is_kept(self):
        # Leg där bara vinnaren registrerats räknas i resultatet
        leg = {'endFlag': 1, 'winner': 1, 'playerData': [[START], [START]]}
        assert not CupImporter._is_unplayed_leg(leg)

    def test_unfinished_leg_with_throws_is_kept(self):
        leg = {'endFlag': 0, 'winner': 0,
               'playerData': [[START, {'score': 60, 'left': 441}], [START]]}
        assert not CupImporter._is_unplayed_leg(leg)
