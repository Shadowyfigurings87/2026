# services/db_reader.py

import sqlite3
from typing import List, Optional, Any
from datetime import datetime, timezone

DB_PATH = "host.db"

def _connect():
    return sqlite3.connect(DB_PATH, check_same_thread=False)

def get_recent_telemetry(limit: int = 100) -> List[dict]:
    conn = _connect()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, timestamp_utc, ts, ministry, payload
        FROM telemetry_raw
        ORDER BY id DESC
        LIMIT ?
    """, (limit,))
    rows = cur.fetchall()
    conn.close()

    return [
        {
            "id": r[0],
            "timestamp_utc": r[1],
            "ts": r[2],
            "ministry": r[3],
            "payload": r[4],
        }
        for r in rows
    ]

def get_recent_rf(limit: int = 100) -> List[dict]:
    conn = _connect()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, timestamp_utc, payload
        FROM telemetry_raw
        WHERE ministry = 'alfa'
        ORDER BY id DESC
        LIMIT ?
    """, (limit,))
    rows = cur.fetchall()
    conn.close()

    out = []
    for r in rows:
        payload = r[2]
        out.append({
            "id": r[0],
            "timestamp_utc": r[1],
            "payload": payload,
        })
    return out

def get_arduino_state() -> Optional[dict]:
    conn = _connect()
    cur = conn.cursor()
    cur.execute("""
        SELECT timestamp_utc, payload
        FROM telemetry_raw
        WHERE ministry = 'arduino'
        ORDER BY id DESC
        LIMIT 1
    """)
    row = cur.fetchone()
    conn.close()

    if not row:
        return None

    return {
        "timestamp_utc": row[0],
        "state": row[1],
    }

def get_health_summary() -> dict:
    conn = _connect()
    cur = conn.cursor()

    # heartbeat
    cur.execute("""
        SELECT timestamp_utc
        FROM telemetry_raw
        WHERE ministry = 'heartbeat'
        ORDER BY id DESC
        LIMIT 1
    """)
    hb = cur.fetchone()

    # watchdog
    cur.execute("""
        SELECT timestamp_utc
        FROM telemetry_raw
        WHERE ministry = 'watchdog'
        ORDER BY id DESC
        LIMIT 1
    """)
    wd = cur.fetchone()

    conn.close()

    now = datetime.now(timezone.utc)

    def age(ts):
        if not ts:
            return None
        try:
            dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
            return (now - dt).total_seconds()
        except:
            return None

    return {
        "heartbeat_age_sec": age(hb[0]) if hb else None,
        "watchdog_age_sec": age(wd[0]) if wd else None,
        "last_heartbeat": hb[0] if hb else None,
        "last_watchdog": wd[0] if wd else None,
    }

def get_system_stats() -> dict:
    # Placeholder — will be replaced with real metrics later
    return {
        "ingest_rate": 0.0,
        "db_queue_depth": 0,
        "uptime_sec": 0.0,
    }
