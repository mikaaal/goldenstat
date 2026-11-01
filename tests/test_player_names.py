"""Tests for how cup player names are stored and merged."""
import sqlite3
from pathlib import Path

from apply_migrations import apply_migrations
from cup_database import CupDatabase

MIGRATIONS = str(Path(__file__).resolve().parent.parent / "migrations" / "cups")


class TestNormalizePlayerName:
    def test_club_after_full_name_is_dropped(self):
        assert CupDatabase.normalize_player_name("Linus Dellby (Bålsta Dart Club)") == "Linus Dellby"
        assert CupDatabase.normalize_player_name("JOCKE EKNER (AIK)") == "Jocke Ekner"

    def test_truncated_club_is_dropped(self):
        assert CupDatabase.normalize_player_name("Dennis Smedberg (nynäshamns Dartförening...") \
            == "Dennis Smedberg"

    def test_single_name_keeps_club(self):
        assert CupDatabase.normalize_player_name("Micke (hdc)") == "Micke (hdc)"

    def test_name_without_club_is_unchanged(self):
        assert CupDatabase.normalize_player_name("anna-lena vilén") == "Anna-Lena Vilén"

    def test_seeding_before_name_is_dropped(self):
        assert CupDatabase.normalize_player_name("16Jonas Norling") == "Jonas Norling"
        assert CupDatabase.normalize_player_name("30Per-Åke Edström") == "Per-Åke Edström"
        assert CupDatabase.normalize_player_name("2 Albin Lindmark") == "Albin Lindmark"

    def test_nickname_with_number_is_kept(self):
        assert CupDatabase.normalize_player_name("180x2") == "180x2"
        assert CupDatabase.normalize_player_name("100%") == "100%"
        assert CupDatabase.normalize_player_name("Micke 170") == "Micke 170"
        assert CupDatabase.normalize_player_name("Wc1") == "Wc1"


def _db(tmp_path, players):
    path = str(tmp_path / "cups.db")
    CupDatabase(path)
    conn = sqlite3.connect(path)
    conn.execute("INSERT INTO tournaments (id, tdid, title) VALUES (1, 't_a', 'Cup')")
    for pid, name in players:
        conn.execute("INSERT INTO players (id, name) VALUES (?, ?)", (pid, name))
        conn.execute("INSERT INTO participants (id, tournament_id, tpid, name) VALUES (?, 1, ?, ?)",
                     (pid, f"tp{pid}", name))
        conn.execute("INSERT INTO participant_players (participant_id, player_id) VALUES (?, ?)",
                     (pid, pid))
    conn.commit()
    return path, conn


def _mappings(conn):
    return {a: (c, n) for a, c, n in conn.execute(
        "SELECT alias_player_id, canonical_player_id, canonical_name FROM cup_player_mappings")}


class TestMergeMigrations:
    def test_club_variants_join_the_plain_name(self, tmp_path):
        path, conn = _db(tmp_path, [
            (1, "Linus Dellby"),
            (2, "Linus Dellby (Bålsta Dart Club)"),
            (3, "Jocke Ekner (AIK)"),
            (4, "Jocke Ekner (AIK Dartförening)"),
            (5, "Micke (hdc)"),
        ])
        apply_migrations(path, MIGRATIONS)

        names = dict(conn.execute("SELECT id, name FROM players"))
        assert names[3] == "Jocke Ekner"  # nobody had the plain name, so the first variant takes it
        assert names[5] == "Micke (hdc)"
        assert _mappings(conn) == {2: (1, "Linus Dellby"), 4: (3, "Jocke Ekner")}
        links = dict(conn.execute("SELECT participant_id, player_id FROM participant_players"))
        assert links == {1: 1, 2: 1, 3: 3, 4: 3, 5: 5}

    def test_alias_chains_point_at_the_final_player(self, tmp_path):
        path, conn = _db(tmp_path, [
            (1, "John Westerlund"),
            (2, "John Vesterlund"),
            (3, "John Vesterlund (AIK Dartförening)"),
        ])
        conn.execute("""INSERT INTO cup_player_mappings
                        (alias_player_id, canonical_player_id, alias_name, canonical_name)
                        VALUES (2, 1, 'John Vesterlund', 'John Westerlund')""")
        conn.commit()
        apply_migrations(path, MIGRATIONS)

        assert _mappings(conn) == {2: (1, "John Westerlund"), 3: (1, "John Westerlund")}

    def test_seeded_names_join_the_player_without_number(self, tmp_path):
        path, conn = _db(tmp_path, [(170, "Jonas Norling"), (7455, "16jonas Norling")])
        apply_migrations(path, MIGRATIONS)

        assert _mappings(conn) == {7455: (170, "Jonas Norling")}
        links = dict(conn.execute("SELECT participant_id, player_id FROM participant_players"))
        assert links == {170: 170, 7455: 170}
