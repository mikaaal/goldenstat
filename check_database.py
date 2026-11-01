#!/usr/bin/env python3
"""
Check that downloaded SQLite databases are whole.

A download that is cut off can still leave a file behind, and the site then
fails with "database disk image is malformed". The Docker build runs this on
each database so that such a file stops the build instead of being deployed.

Usage:
    python check_database.py cups.db [goldenstat.db ...]
"""
import sqlite3
import sys


def check(path: str) -> str:
    """'ok', or what is wrong with the database at path."""
    try:
        conn = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
        try:
            # An empty file is a valid database too, so it must also have tables
            if not conn.execute("SELECT COUNT(*) FROM sqlite_master").fetchone()[0]:
                return "no tables"
            return conn.execute("PRAGMA quick_check").fetchone()[0]
        finally:
            conn.close()
    except sqlite3.Error as e:
        return str(e)


def main() -> int:
    failed = False
    for path in sys.argv[1:]:
        result = check(path)
        print(f"{path}: {result}")
        failed |= result != "ok"
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
