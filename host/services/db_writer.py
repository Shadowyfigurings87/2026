# host/services/db_writer.py

import sqlite3
import threading
import queue
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "host.db"

write_queue = queue.Queue()

def db_writer_thread():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    while True:
        stmt, params = write_queue.get()
        try:
            cur.execute(stmt, params)
            conn.commit()
        except Exception as e:
            print(f"[DB] Write error: {e}")

def start_db_writer():
    t = threading.Thread(target=db_writer_thread, daemon=True)
    t.start()
