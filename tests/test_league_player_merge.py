"""Tests for the migration that merges league players registered more than once."""
import sqlite3
from pathlib import Path

MIGRATION = Path(__file__).resolve().parent.parent / "migrations" / "goldenstat" / "027_merge_duplicate_players.sql"

SCHEMA = """
CREATE TABLE players (id INTEGER PRIMARY KEY, name VARCHAR(255) NOT NULL);
CREATE TABLE sub_match_participants (
    id INTEGER PRIMARY KEY, sub_match_id INTEGER NOT NULL, player_id INTEGER NOT NULL,
    team_number INTEGER NOT NULL DEFAULT 1);
CREATE TABLE sub_match_player_mappings (
    id INTEGER PRIMARY KEY, sub_match_id INTEGER NOT NULL, original_player_id INTEGER NOT NULL,
    correct_player_id INTEGER NOT NULL, correct_player_name TEXT NOT NULL,
    UNIQUE(sub_match_id, original_player_id), CHECK(original_player_id != correct_player_id));
CREATE TABLE player_aliases (
    alias_player_id INTEGER PRIMARY KEY, canonical_player_id INTEGER NOT NULL,
    canonical_player_name TEXT NOT NULL, notes TEXT,
    CHECK(alias_player_id != canonical_player_id));
"""


def _db(tmp_path):
    conn = sqlite3.connect(tmp_path / "goldenstat.db")
    conn.executescript(SCHEMA)
    conn.executemany("INSERT INTO players VALUES (?, ?)", [
        (8, "Daniel Carlqvist"), (2358, "Daniel Carlqvist"), (2440, "Daniel Carlqvist"),
        (52, "Oscar Rosén"), (1248, "Oscar Rosen"), (99, "Stefan Johansson"),
    ])
    conn.executemany("INSERT INTO sub_match_participants (sub_match_id, player_id) VALUES (?, ?)", [
        (1, 8), (2, 2358), (3, 2440), (4, 1248), (5, 99),
    ])
    conn.executemany("""INSERT INTO sub_match_player_mappings
                        (sub_match_id, original_player_id, correct_player_id, correct_player_name)
                        VALUES (?, ?, ?, ?)""", [
        (3, 2440, 8, "Daniel Carlqvist"),   # between two ids of the same player
        (2, 2358, 99, "Stefan Johansson"),  # from a duplicate to someone else
        (5, 99, 1248, "Oscar Rosen"),       # to a spelling variant
    ])
    conn.commit()
    conn.executescript(MIGRATION.read_text(encoding="utf-8"))
    return conn


def test_all_matches_end_up_on_the_kept_player(tmp_path):
    conn = _db(tmp_path)
    links = dict(conn.execute("SELECT sub_match_id, player_id FROM sub_match_participants"))
    assert links == {1: 8, 2: 8, 3: 8, 4: 52, 5: 99}


def test_mappings_follow_the_merge(tmp_path):
    conn = _db(tmp_path)
    mappings = set(conn.execute("""SELECT sub_match_id, original_player_id, correct_player_id,
                                          correct_player_name FROM sub_match_player_mappings"""))
    assert mappings == {(2, 8, 99, "Stefan Johansson"), (5, 99, 52, "Oscar Rosén")}


def test_duplicates_become_aliases_so_future_imports_follow(tmp_path):
    conn = _db(tmp_path)
    aliases = dict(conn.execute("SELECT alias_player_id, canonical_player_id FROM player_aliases"))
    assert aliases == {2358: 8, 2440: 8, 1248: 52}


def test_running_twice_changes_nothing(tmp_path):
    conn = _db(tmp_path)
    before = list(conn.execute("SELECT * FROM sub_match_player_mappings ORDER BY id"))
    conn.executescript(MIGRATION.read_text(encoding="utf-8"))
    assert list(conn.execute("SELECT * FROM sub_match_player_mappings ORDER BY id")) == before
