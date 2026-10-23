"""Tests for individual statistics in doubles with a fixed throwing order.

From the 2026/2027 season the first player in each team's order always starts
every leg, so a team's visits alternate order[0], order[1], order[0], ...
"""
from datetime import datetime

import pytest

from database import individual_doubles_stats, visit_throw_order
from new_season_importer import (
    NewSeasonImporter,
    fixed_doubles_order_applies,
    fixed_doubles_order_start,
    individual_doubles_averages,
)

ORDER = [{"oname": "Anna Andersson"}, {"oname": "Bertil Berg"}]
RULE_FROM = datetime(2026, 8, 1)


def _visit(score, left):
    return {"score": score, "left": left}


def _submatch(start=datetime(2026, 9, 15, 19, 0)):
    """Two legs. Leg 1 is won by team 0, whose second player checks out 60 with 2 darts."""
    leg1 = {
        "first": 0,
        "winner": 0,
        "currentRound": 6,
        "playerData": [
            [_visit(0, 501), _visit(60, 441), _visit(100, 341), _visit(140, 201),
             _visit(81, 120), _visit(60, 60), _visit(-2, 0)],
            [_visit(0, 501), _visit(45, 456), _visit(26, 430), _visit(100, 330),
             _visit(41, 289), _visit(85, 204)],
        ],
    }
    # Leg 2 restarts the rotation: order[0] throws the first visit again
    leg2 = {
        "first": 1,
        "winner": 1,
        "currentRound": 2,
        "playerData": [
            [_visit(0, 501), _visit(100, 401), _visit(57, 344)],
            [_visit(0, 501), _visit(60, 441)],
        ],
    }
    return {
        "startTime": int(start.timestamp()),
        "startScore": 501,
        "legData": [leg1, leg2],
        "statsData": [{"order": ORDER}, {"order": ORDER}],
    }


class TestRuleEnabledPerSeries:
    def test_stockholmsserien(self):
        assert fixed_doubles_order_start("goldenstat.db") == RULE_FROM

    def test_full_path_uses_file_name(self):
        assert fixed_doubles_order_start("/tmp/goldenstat_test_x/goldenstat.db") == RULE_FROM

    @pytest.mark.parametrize("db_path", ["riksserien.db", "sommarserien.db", "cups.db"])
    def test_not_confirmed_series(self, db_path):
        assert fixed_doubles_order_start(db_path) is None

    def test_series_without_rule_never_applies(self):
        assert not fixed_doubles_order_applies(_submatch(), ORDER, None)


class TestFixedOrderApplies:
    def test_new_season_doubles(self):
        assert fixed_doubles_order_applies(_submatch(), ORDER, RULE_FROM)

    def test_start_time_in_milliseconds(self):
        submatch = _submatch()
        submatch["startTime"] *= 1000
        assert fixed_doubles_order_applies(submatch, ORDER, RULE_FROM)

    def test_before_rule_change(self):
        assert not fixed_doubles_order_applies(_submatch(datetime(2026, 4, 17, 19, 0)), ORDER, RULE_FROM)

    def test_singles(self):
        assert not fixed_doubles_order_applies(_submatch(), ORDER[:1], RULE_FROM)

    def test_missing_player_name(self):
        assert not fixed_doubles_order_applies(_submatch(), [ORDER[0], {"oname": "Unknown"}], RULE_FROM)

    def test_leg_without_start_marker(self):
        submatch = _submatch()
        submatch["legData"][1]["playerData"][0].pop(0)
        assert not fixed_doubles_order_applies(submatch, ORDER, RULE_FROM)


class TestIndividualAverages:
    def test_visits_alternate_and_restart_each_leg(self):
        submatch = _submatch()
        # Anna: 60+140+60 (leg 1) + 100 (leg 2) = 360 on 12 darts
        # Bertil: 100+81 + checkout 60 on 2 darts (leg 1) + 57 (leg 2) = 298 on 11 darts
        assert individual_doubles_averages(submatch["legData"], 0) == [90.0, 81.27]
        # 45+100+85+60 = 290 on 12 darts, 26+41 = 67 on 6 darts
        assert individual_doubles_averages(submatch["legData"], 1) == [72.5, 33.5]

    def test_visit_throw_order(self):
        assert visit_throw_order(1) is None  # start marker
        assert [visit_throw_order(r) for r in (2, 3, 4, 5)] == [0, 1, 0, 1]


class _RecordingDb:
    """Stands in for DartDatabase and keeps the rows import_leg would write."""

    def __init__(self):
        self.throws = []
        self.legs = 0

    def insert_leg(self, leg_info):
        self.legs += 1
        return self.legs

    def insert_throw(self, throw_info):
        self.throws.append(throw_info)


def _stored_throws(legs):
    importer = NewSeasonImporter.__new__(NewSeasonImporter)
    importer.db = _RecordingDb()
    for leg_number, leg in enumerate(legs, 1):
        importer.import_leg(1, leg_number, leg)
    return importer.db.throws


class TestImportAndReadAgree:
    """The average stored at import must match what the routes compute from stored throws."""

    @pytest.mark.parametrize("team_index", [0, 1])
    def test_stored_throws_give_same_average(self, team_index):
        submatch = _submatch()
        team_throws = [
            t for t in _stored_throws(submatch["legData"])
            if t["team_number"] == team_index + 1
            # Routes read throws without the start marker
            and not (t["score"] == 0 and t["round_number"] == 1)
        ]

        expected = individual_doubles_averages(submatch["legData"], team_index)
        from_db = [individual_doubles_stats(team_throws, position)["average"] for position in (0, 1)]
        assert from_db == expected

    def test_checkout_counts_for_the_player_who_threw_it(self):
        submatch = _submatch()
        team_throws = [t for t in _stored_throws(submatch["legData"][:1]) if t["team_number"] == 1]

        bertil = individual_doubles_stats(team_throws, 1)
        anna = individual_doubles_stats(team_throws, 0)
        assert bertil["checkouts"] == 1
        assert anna["checkouts"] == 0
        assert bertil["darts"] == 8
