# host/services/db_writer.py

from host.logs.wrappers import log_db

import sqlite3
import threading
import queue
import time
from pathlib import Path

from host.services.metrics import (
    db_writes_total,
    db_write_errors_total,
    db_write_latency_ms,
    db_write_latency_histogram,
)

DB_PATH = Path(__file__).resolve().parent.parent / "host.db"

# Global write queue
write_queue = queue.Queue()


def db_writer_thread():
    """
    Dedicated SQLite writer thread.
    Ensures all writes happen sequentially and safely.
    """
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    conn.execute("PRAGMA busy_timeout=5000;")
    cur = conn.cursor()

    while True:
        stmt, params = write_queue.get()
        start = time.perf_counter()

        try:
            cur.execute(stmt, params)
            conn.commit()
            db_writes_total.inc()

        except Exception as e:
            log_db("db_write_error", error=str(e), stmt=stmt)
            db_write_errors_total.inc()

        finally:
            duration = time.perf_counter() - start
            db_write_latency_ms.set(duration * 1000.0)
            db_write_latency_histogram.observe(duration)


def start_db_writer():
    """
    Launch the DB writer thread.
    """
    t = threading.Thread(target=db_writer_thread, daemon=True)
    t.start()
