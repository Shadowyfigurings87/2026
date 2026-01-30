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

DB_PATH = Path(__file__).resolve().parent.parent / "host.host.db"

# Global write queue
write_queue = queue.Queue()


# ============================================================
# INTERNAL: Initialize tables (safety net)
# ============================================================

def _init_tables(conn):
    """
    Safety net: ensures required tables exist.
    Your init_db.py already creates them, but this prevents
    runtime crashes if init_db wasn't run.
    """
    cur = conn.cursor()

    # Raw telemetry archive
    cur.execute("""
        CREATE TABLE IF NOT EXISTS telemetry_raw (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp_utc TEXT NOT NULL,
            ts REAL NOT NULL,
            ministry TEXT NOT NULL,
            payload TEXT NOT NULL
        )
    """)

    # Arduino decoded state
    cur.execute("""
        CREATE TABLE IF NOT EXISTS arduino_state (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            rpm REAL,
            throttle REAL,
            direction TEXT,
            pwm REAL,
            ts TEXT,
            raw TEXT
        )
    """)

    # ESP32 decoded state
    cur.execute("""
        CREATE TABLE IF NOT EXISTS esp32_state (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            status TEXT,
            queue_pressure REAL,
            ts TEXT,
            raw TEXT
        )
    """)

    # GPS positions (breadcrumb trail)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS gps_positions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ts REAL,
            timestamp TEXT,
            lat REAL,
            lon REAL
        )
    """)

    conn.commit()


# ============================================================
# DB WRITER THREAD
# ============================================================

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
# RAW TELEMETRY INSERT
# ============================================================

def write_raw_telemetry(timestamp_utc: str, ts: float, ministry: str, payload: dict):
    """
    Insert raw telemetry into telemetry_raw.
    """
    write_queue.put((
        """
        INSERT INTO telemetry_raw (timestamp_utc, ts, ministry, payload)
        VALUES (?, ?, ?, ?)
        """,
        (timestamp_utc, ts, ministry, json.dumps(payload)),
    ))


# ============================================================
# ESP32 UPSERT
# ============================================================

def upsert_esp32_state(status: str, queue_pressure: float | None, ts: str, raw: dict):
    """
    Store the latest ESP32 state in a single-row table.
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


# ============================================================
# ARDUINO UPSERT
# ============================================================

def upsert_arduino_state(rpm: float, throttle: float, direction: str, pwm: float, ts: str, raw: dict):
    """
    Store the latest Arduino state in a single-row table.
    """
    write_queue.put((
        """
        INSERT INTO arduino_state (id, rpm, throttle, direction, pwm, ts, raw)
        VALUES (1, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET
            rpm = excluded.rpm,
            throttle = excluded.throttle,
            direction = excluded.direction,
            pwm = excluded.pwm,
            ts = excluded.ts,
            raw = excluded.raw
        """,
        (rpm, throttle, direction, pwm, ts, json.dumps(raw)),
    ))


# ============================================================
# GPS POSITION INSERT
# ============================================================

def insert_gps_position(lat: float, lon: float, ts: float, timestamp: str):
    """
    Insert a GPS coordinate into gps_positions.
    """
    write_queue.put((
        """
        INSERT INTO gps_positions (ts, timestamp, lat, lon)
        VALUES (?, ?, ?, ?)
        """,
        (ts, timestamp, lat, lon),
    ))
