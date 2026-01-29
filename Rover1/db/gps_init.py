# Rover1/db/gps_init.py

import os
import sqlite3

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "..", "data", "gps.db")
DB_PATH = os.path.abspath(DB_PATH)

os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)


def init_gps_db():
    """
    Creates the GPS database and table if they do not exist.
    Safe to run multiple times.
    """

    # Ensure the data directory exists
    data_dir = os.path.dirname(DB_PATH)
    if not os.path.exists(data_dir):
        os.makedirs(data_dir, exist_ok=True)

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS gps (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ts REAL NOT NULL,
            lat REAL NOT NULL,
            lon REAL NOT NULL
        );
    """)

    conn.commit()
    conn.close()
    print(f"[GPS Init] Initialized GPS database at {DB_PATH}")
