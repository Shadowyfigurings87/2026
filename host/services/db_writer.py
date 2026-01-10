import sqlite3
import threading
import queue
from pathlib import Path
from services.metrics import db_queue_depth, db_write_latency
import time

DB_PATH = Path(__file__).resolve().parent.parent / "host.db"

write_queue = queue.Queue()

def db_writer_thread():
    # Thread-safe SQLite connection
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    conn.execute("PRAGMA busy_timeout=5000;")
    cur = conn.cursor()

    while True:
        # Update queue depth metric
        db_queue_depth.set(write_queue.qsize())

        stmt, params = write_queue.get()

        try:
            start = time.time()

            cur.execute(stmt, params)
            conn.commit()

            # Record write latency
            db_write_latency.observe(time.time() - start)

        except Exception as e:
            print(f"[DB] Write error: {e}")

def start_db_writer():
    t = threading.Thread(target=db_writer_thread, daemon=True)
    t.start()
