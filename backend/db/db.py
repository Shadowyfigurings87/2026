import sqlite3
from pathlib import Path

# Point to your existing rf_archive.db
DB_PATH = Path(__file__).resolve().parent.parent / "data" / "rf_archive.db"

def execute_db(sql, params=()):
    """Run a single SQL statement with parameters against rf_archive.db."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute(sql, params)
        conn.commit()
    finally:
        conn.close()
