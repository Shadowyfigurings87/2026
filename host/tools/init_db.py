#!/usr/bin/env python3
"""
Initialize the Host SQLite database and required directories.
Creates:
  - host/host.db
  - host/data/frames/
"""

import sqlite3
from pathlib import Path
from host.logs.logging import info

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "host.db"
FRAMES_DIR = BASE_DIR / "data" / "frames"

SCHEMA = [
    # ---------------------------------------------------------
    # Unified raw telemetry (metadata only)
    # ---------------------------------------------------------
    """
    CREATE TABLE IF NOT EXISTS telemetry_raw (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp_utc TEXT NOT NULL,
        ts REAL NOT NULL,
        ministry TEXT NOT NULL,
        payload JSON NOT NULL
    );
    """,
    "CREATE INDEX IF NOT EXISTS idx_telemetry_ministry ON telemetry_raw(ministry);",
    "CREATE INDEX IF NOT EXISTS idx_telemetry_ts ON telemetry_raw(ts);",

    # ---------------------------------------------------------
    # Decoded Arduino state (canonical 2026 table)
    # Single row: id = 1
    # ---------------------------------------------------------
    """
    CREATE TABLE IF NOT EXISTS arduino_state (
        id INTEGER PRIMARY KEY CHECK (id = 1),
        rpm REAL,
        throttle REAL,
        direction TEXT,
        pwm REAL,
        ts TEXT,
        raw JSON
    );
    """,

    # ---------------------------------------------------------
    # Decoded ESP32 state (canonical 2026 table)
    # Single row: id = 1
    # ---------------------------------------------------------
    """
    CREATE TABLE IF NOT EXISTS esp32_state (
        id INTEGER PRIMARY KEY CHECK (id = 1),
        status TEXT,
        queue_pressure REAL,
        ts TEXT,
        raw JSON
    );
    """,

    # ---------------------------------------------------------
    # Command log (Host → Rover1)
    # ---------------------------------------------------------
    """
    CREATE TABLE IF NOT EXISTS command_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp_utc TEXT NOT NULL,
        ts REAL NOT NULL,
        ministry TEXT NOT NULL,
        command TEXT NOT NULL,
        value TEXT,
        ack TEXT,
        error TEXT
    );
    """,
    "CREATE INDEX IF NOT EXISTS idx_cmd_ts ON command_log(ts);",

    # ---------------------------------------------------------
    # Health events (heartbeat, watchdog, queue pressure)
    # ---------------------------------------------------------
    """
    CREATE TABLE IF NOT EXISTS health_events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp_utc TEXT NOT NULL,
        ts REAL NOT NULL,
        event TEXT NOT NULL,
        data JSON
    );
    """,
    "CREATE INDEX IF NOT EXISTS idx_health_ts ON health_events(ts);",

    # ---------------------------------------------------------
    # Camera frame index (frames stored on disk)
    # ---------------------------------------------------------
    """
    CREATE TABLE IF NOT EXISTS camera_frames (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp_utc TEXT NOT NULL,
        ts REAL NOT NULL,
        ministry TEXT NOT NULL,
        frame_path TEXT NOT NULL,
        width INTEGER,
        height INTEGER,
        format TEXT,
        metadata JSON
    );
    """,
    "CREATE INDEX IF NOT EXISTS idx_cam_ts ON camera_frames(ts);",

    # ---------------------------------------------------------
    # RF events (Alfa1200AU, ESP32, future radios)
    # ---------------------------------------------------------
    """
    CREATE TABLE IF NOT EXISTS rf_events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp_utc TEXT NOT NULL,
        ts REAL NOT NULL,
        ministry TEXT NOT NULL,
        event_type TEXT NOT NULL,
        frequency REAL,
        rssi REAL,
        modulation TEXT,
        payload BLOB,
        metadata JSON
    );
    """,
    "CREATE INDEX IF NOT EXISTS idx_rf_ts ON rf_events(ts);",
    "CREATE INDEX IF NOT EXISTS idx_rf_freq ON rf_events(frequency);",

    # ---------------------------------------------------------
    # System log (host-side)
    # ---------------------------------------------------------
    """
    CREATE TABLE IF NOT EXISTS system_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp_utc TEXT NOT NULL,
        level TEXT NOT NULL,
        message TEXT NOT NULL,
        metadata JSON
    );
    """
]


def main():
    info("init_db_starting")

    # Ensure directories exist
    FRAMES_DIR.mkdir(parents=True, exist_ok=True)
    info("init_db_frames_dir_ready", path=str(FRAMES_DIR))

    # Create SQLite DB
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    for stmt in SCHEMA:
        cur.execute(stmt)

    # Initialize single-row state tables
    cur.execute("INSERT OR IGNORE INTO arduino_state (id) VALUES (1);")
    cur.execute("INSERT OR IGNORE INTO esp32_state (id) VALUES (1);")

    conn.commit()
    conn.close()

    info("init_db_complete", db_path=str(DB_PATH))


if __name__ == "__main__":
    main()
