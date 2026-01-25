# host/services/db_reader.py

import sqlite3
import json
from typing import List, Optional, Any
from datetime import datetime, timezone
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "host.host.db"


def _connect():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


# ============================================================
# RAW TELEMETRY
# ============================================================

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

    out = []
    for r in rows:
        try:
            payload = json.loads(r["payload"])
        except Exception:
            payload = r["payload"]

        out.append({
            "id": r["id"],
            "timestamp_utc": r["timestamp_utc"],
            "ts": r["ts"],
            "ministry": r["ministry"],
            "payload": payload,
        })

    return out


# ============================================================
# RF TELEMETRY
# ============================================================

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
        try:
            payload = json.loads(r["payload"])
        except Exception:
            payload = r["payload"]

        out.append({
            "id": r["id"],
            "timestamp_utc": r["timestamp_utc"],
            "payload": payload,
        })

    return out


# ============================================================
# ARDUINO (legacy fallback from telemetry_raw)
# ============================================================

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

    try:
        payload = json.loads(row["payload"])
    except Exception:
        payload = row["payload"]

    return {
        "timestamp_utc": row["timestamp_utc"],
        "state": payload,
    }


# ============================================================
# ARDUINO (new decoded state table)
# ============================================================

def get_latest_arduino_state() -> Optional[dict]:
    """
    Returns the latest decoded Arduino state from arduino_state.
    """
    conn = _connect()
    cur = conn.cursor()

    cur.execute("""
        SELECT rpm, throttle, direction, pwm, ts, raw
        FROM arduino_state
        WHERE id = 1
    """)

    row = cur.fetchone()
    conn.close()

    if not row:
        return None

    try:
        raw = json.loads(row["raw"]) if row["raw"] else None
    except Exception:
        raw = row["raw"]

    return {
        "rpm": row["rpm"],
        "throttle": row["throttle"],
        "direction": row["direction"],
        "pwm": row["pwm"],
        "ts": row["ts"],
        "raw": raw,
    }


def get_latest_arduino_raw() -> Optional[sqlite3.Row]:
    """
    Returns the latest raw Arduino telemetry row from telemetry_raw.
    """
    conn = _connect()
    cur = conn.cursor()

    cur.execute("""
        SELECT id, payload
        FROM telemetry_raw
        WHERE ministry='arduino'
        ORDER BY id DESC
        LIMIT 1
    """)

    row = cur.fetchone()
    conn.close()
    return row


# ============================================================
# ESP32 (new ministry)
# ============================================================

def get_esp32_state() -> Optional[dict]:
    conn = _connect()
    cur = conn.cursor()

    cur.execute("""
        SELECT status, queue_pressure, ts, raw
        FROM esp32_state
        WHERE id = 1
    """)

    row = cur.fetchone()
    conn.close()

    if not row:
        return None

    try:
        raw = json.loads(row["raw"])
    except Exception:
        raw = row["raw"]

    return {
        "status": row["status"],
        "queue_pressure": row["queue_pressure"],
        "ts": row["ts"],
        "raw": raw,
    }


# ============================================================
# HEALTH SUMMARY
# ============================================================

def get_health_summary() -> dict:
    conn = _connect()
    cur = conn.cursor()

    cur.execute("""
        SELECT timestamp_utc
        FROM telemetry_raw
        WHERE ministry = 'heartbeat'
        ORDER BY id DESC
        LIMIT 1
    """)
    hb = cur.fetchone()

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
        except Exception:
            return None

    return {
        "heartbeat_age_sec": age(hb["timestamp_utc"]) if hb else None,
        "watchdog_age_sec": age(wd["timestamp_utc"]) if wd else None,
        "last_heartbeat": hb["timestamp_utc"] if hb else None,
        "last_watchdog": wd["timestamp_utc"] if wd else None,
    }


# ============================================================
# SYSTEM STATS (placeholder)
# ============================================================

def get_system_stats() -> dict:
    return {
        "ingest_rate": 0.0,
        "db_queue_depth": 0,
        "uptime_sec": 0.0,
    }
