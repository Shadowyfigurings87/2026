# host/services/db_writer.py

from host.logs.wrappers import log_system

import sqlite3
import threading
import queue
import time
from pathlib import Path
import json

from host.services.metrics import (
    db_writes_total,
    db_write_errors_total,
    db_write_latency_ms,
    db_write_latency_histogram,
)

DB_PATH = Path(__file__).resolve().parent.parent / "host.db"

# Global write queue
write_queue = queue.Queue()


def _init_tables(conn):
    """
    Ensure required tables exist.
    """
    cur = conn.cursor()

    # Table for raw telemetry (already exists in your system)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS telemetry_raw (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp_utc TEXT,
            ts REAL,
            ministry TEXT,
            payload TEXT
        )
    """)

    # NEW: Table for latest ESP32 state
    cur.execute("""
        CREATE TABLE IF NOT EXISTS esp32_state (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            status TEXT,
            queue_pressure INTEGER,
            ts TEXT,
            raw TEXT
        )
    """)

    conn.commit()


def db_writer_thread():
    """
    Dedicated SQLite writer thread.
    Ensures all writes happen sequentially and safely.
    """
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    conn.execute("PRAGMA busy_timeout=5000;")

    _init_tables(conn)

    cur = conn.cursor()

    while True:
        stmt, params = write_queue.get()
        start = time.perf_counter()

        try:
            cur.execute(stmt, params)
            conn.commit()
            db_writes_total.inc()

        except Exception as e:
            log_system("db_write_error", error=str(e), stmt=stmt)
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


# ============================================================
# NEW: ESP32 UPSERT
# ============================================================

def upsert_esp32_state(status: str, queue_pressure: int | None, ts: str, raw: dict):
    """
    Store the latest ESP32 state in a single-row table.
    Uses INSERT OR REPLACE to maintain exactly one row.
    """
    write_queue.put((
        """
        INSERT INTO esp32_state (id, status, queue_pressure, ts, raw)
        VALUES (1, ?, ?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET
            status = excluded.status,
            queue_pressure = excluded.queue_pressure,
            ts = excluded.ts,
            raw = excluded.raw
        """,
        (status, queue_pressure, ts, json.dumps(raw)),
    ))
