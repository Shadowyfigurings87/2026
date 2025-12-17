import sqlite3
import threading
from queue import Queue
from utils.config import get_db_path

# Global write queue used by all producers (ingest, anomaly engine, etc.)
db_write_queue: Queue = Queue()
DB_PATH = get_db_path()

def db_writer():
    """
    Dedicated writer thread:
    - consumes SQL statements from db_write_queue
    - executes them against sovereign.db
    - commits after each write
    """
    conn = sqlite3.connect(DB_PATH, timeout=5.0, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON;")
    conn.execute("PRAGMA busy_timeout=5000;")
    cur = conn.cursor()

    print("[DB] Writer thread started")

    while True:
        sql, params = db_write_queue.get()
        try:
            cur.execute(sql, params)
            conn.commit()
            # Debug log for visibility
            if sql.strip().upper().startswith("INSERT INTO frames"):
                print(f"[DB] Inserted frame src={params[6]} dst={params[7]} ch={params[10]} rssi={params[11]}")
        except Exception as e:
            print(f"[DB] Writer error: {e} | SQL={sql} | params={params}")
