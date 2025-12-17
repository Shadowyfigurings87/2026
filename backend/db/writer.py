# db/writer.py

import sqlite3
import threading
from write_queue import db_write_queue
from utils.config import get_db_path

DB_PATH = get_db_path()

def db_writer_loop():
    conn = sqlite3.connect(DB_PATH, timeout=5.0, check_same_thread=False)
    conn.execute("PRAGMA journal_mode=WAL;")
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

            # Optional debug visibility
            if sql.strip().upper().startswith("INSERT INTO FRAMES"):
                print(f"[DB] Inserted frame src={params[6]} dst={params[7]} ch={params[10]} rssi={params[11]}")

        except Exception as e:
            print(f"[DB] Writer error: {e} | SQL={sql} | params={params}")


def start_db_writer():
    t = threading.Thread(target=db_writer_loop, daemon=True)
    t.start()
