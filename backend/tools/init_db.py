# tools/init_db.py

import sqlite3
from pathlib import Path
from utils.config import get_db_path

SQL_PATH = Path(__file__).resolve().parent / "init_rf_archive.sql"


def main():
    db_path = get_db_path()
    print(f"Initializing database at: {db_path}")

    sql = SQL_PATH.read_text()

    conn = sqlite3.connect(db_path)
    conn.executescript(sql)
    conn.commit()
    conn.close()

    print("Database initialized successfully.")


if __name__ == "__main__":
    main()
