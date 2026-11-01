"""Tests for the check of downloaded databases in the Docker build."""
import sqlite3

from check_database import check


def _db(tmp_path):
    path = tmp_path / "cups.db"
    conn = sqlite3.connect(path)
    conn.execute("CREATE TABLE players (id INTEGER PRIMARY KEY, name TEXT)")
    conn.executemany("INSERT INTO players (name) VALUES (?)", [(f"Spelare {i}" * 50,) for i in range(2000)])
    conn.commit()
    conn.close()
    return path


def test_whole_database_is_ok(tmp_path):
    assert check(str(_db(tmp_path))) == "ok"


def test_cut_off_download_is_caught(tmp_path):
    path = _db(tmp_path)
    data = path.read_bytes()
    path.write_bytes(data[:len(data) // 2])
    assert check(str(path)) != "ok"


def test_empty_file_is_caught(tmp_path):
    path = tmp_path / "cups.db"
    path.write_bytes(b"")
    assert check(str(path)) == "no tables"


def test_error_page_is_caught(tmp_path):
    path = tmp_path / "cups.db"
    path.write_text("<html>Not Found</html>")
    assert check(str(path)) == "file is not a database"
