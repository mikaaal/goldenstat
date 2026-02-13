#!/usr/bin/env python3
"""
Applicera SQL-migreringar på en SQLite-databas.

Skapar en _migrations-tabell som spårar vilka migreringar som körts.
Idempotent — säkert att köra flera gånger.

Usage:
    python apply_migrations.py <db_path> <migrations_dir>
    python apply_migrations.py goldenstat.db migrations/goldenstat
    python apply_migrations.py cups.db migrations/cups
"""
import sqlite3
import sys
from pathlib import Path


def apply_migrations(db_path: str, migrations_dir: str) -> int:
    """Applicera alla nya migreringar från migrations_dir på db_path.

    Returns: antal nya migreringar som kördes.
    """
    migrations_path = Path(migrations_dir)
    if not migrations_path.is_dir():
        print(f"[MIGRATIONS] Katalog saknas: {migrations_dir} — hoppar över")
        return 0

    # Samla alla .sql-filer sorterade efter filnamn (001_, 002_, ...)
    sql_files = sorted(migrations_path.glob("*.sql"))
    if not sql_files:
        print(f"[MIGRATIONS] Inga .sql-filer i {migrations_dir}")
        return 0

    conn = sqlite3.connect(db_path)
    try:
        # Skapa _migrations-tabell om den inte finns
        conn.execute("""
            CREATE TABLE IF NOT EXISTS _migrations (
                filename TEXT PRIMARY KEY,
                applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()

        # Hämta redan körda migreringar
        applied = {row[0] for row in conn.execute("SELECT filename FROM _migrations").fetchall()}

        applied_count = 0
        for sql_file in sql_files:
            if sql_file.name in applied:
                continue

            print(f"[MIGRATIONS] Kör {sql_file.name} på {db_path}...")
            sql = sql_file.read_text(encoding="utf-8")

            if sql.strip():
                conn.executescript(sql)

            conn.execute("INSERT INTO _migrations (filename) VALUES (?)", (sql_file.name,))
            conn.commit()
            applied_count += 1

        if applied_count:
            print(f"[MIGRATIONS] {applied_count} migrering(ar) applicerade på {db_path}")
        else:
            print(f"[MIGRATIONS] {db_path} är redan uppdaterad")

        return applied_count
    finally:
        conn.close()


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python apply_migrations.py <db_path> <migrations_dir>")
        sys.exit(1)

    db_path = sys.argv[1]
    migrations_dir = sys.argv[2]

    if not Path(db_path).exists():
        print(f"[MIGRATIONS] Databas saknas: {db_path} — hoppar över")
        sys.exit(0)

    apply_migrations(db_path, migrations_dir)
