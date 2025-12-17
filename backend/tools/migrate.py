# tools/migrate.py

import sqlite3
from pathlib import Path
from utils.config import get_db_path

MIGRATIONS_DIR = Path(__file__).resolve().parent.parent / "migrations"


def ensure_migration_table(conn):
    conn.execute("""
        CREATE TABLE IF NOT EXISTS schema_migrations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT UNIQUE NOT NULL,
            applied_at TEXT NOT NULL
        )
    """)
    conn.commit()


def get_applied_migrations(conn) -> set[str]:
    ensure_migration_table(conn)
    rows = conn.execute("SELECT filename FROM schema_migrations").fetchall()
    return {r[0] for r in rows}


def apply_migration(conn, filename: str):
    path = MIGRATIONS_DIR / filename
    sql = path.read_text()
    print(f"[+] Applying migration: {filename}")
    conn.executescript(sql)
    conn.execute(
        "INSERT INTO schema_migrations (filename, applied_at) VALUES (?, datetime('now'))",
        (filename,),
    )
    conn.commit()


def main():
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)

    applied = get_applied_migrations(conn)

    files = sorted(
        f.name for f in MIGRATIONS_DIR.iterdir()
        if f.is_file() and f.suffix == ".sql"
    )

    for filename in files:
        if filename in applied:
            continue
        apply_migration(conn, filename)

    conn.close()
    print("[+] Migration complete.")


if __name__ == "__main__":
    main()
