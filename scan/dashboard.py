#!/usr/bin/env python3
import sqlite3
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional

DB_PATH = "/home/zachariah/2026/scan/data/rf_archive.db"

app = FastAPI(title="RF Intelligence Dashboard API", version="14.0")

# Allow any frontend to connect (React, Vue, Svelte, etc.)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

def query(sql: str, params: tuple = ()):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute(sql, params)
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows

# ---------------------------------------------------------
# Root
# ---------------------------------------------------------
@app.get("/")
def root():
    return {
        "status": "ok",
        "message": "RF Intelligence Dashboard API (Phase 14)",
        "endpoints": [
            "/frames/recent",
            "/alerts/recent",
            "/channels/recent",
            "/sensors/status",
            "/identity/components",
            "/system/health"
        ]
    }

# ---------------------------------------------------------
# Frames
# ---------------------------------------------------------
@app.get("/frames/recent")
def recent_frames(limit: int = 50):
    return query(
        """
        SELECT timestamp, frame_type, subtype, src_mac, dst_mac, bssid,
               channel, rssi, sensor_id, sensor_component_role
        FROM frames
        ORDER BY id DESC
        LIMIT ?
        """,
        (limit,)
    )

# ---------------------------------------------------------
# Alerts
# ---------------------------------------------------------
@app.get("/alerts/recent")
def recent_alerts(limit: int = 50):
    return query(
        """
        SELECT timestamp, alert_type, mac, sensor_id, component_role,
               severity, description
        FROM alerts
        ORDER BY id DESC
        LIMIT ?
        """,
        (limit,)
    )

# ---------------------------------------------------------
# Channel Metrics
# ---------------------------------------------------------
@app.get("/channels/recent")
def recent_channel_metrics(limit: int = 50):
    return query(
        """
        SELECT timestamp, channel, sensor_id, component_role, activity_score
        FROM channel_metrics
        ORDER BY id DESC
        LIMIT ?
        """,
        (limit,)
    )

# ---------------------------------------------------------
# Sensor Heartbeats
# ---------------------------------------------------------
@app.get("/sensors/status")
def sensor_status():
    return query(
        """
        SELECT sensor_id, last_seen, component_mac, component_role
        FROM sensor_status
        ORDER BY last_seen DESC
        """
    )

# ---------------------------------------------------------
# Identity Registry
# ---------------------------------------------------------
@app.get("/identity/components")
def identity_components():
    return query(
        """
        SELECT sensor_id, mac, role, description
        FROM sensor_components
        ORDER BY sensor_id ASC
        """
    )

# ---------------------------------------------------------
# System Health
# ---------------------------------------------------------
@app.get("/system/health")
def system_health():
    frames = query("SELECT COUNT(*) AS count FROM frames")[0]["count"]
    alerts = query("SELECT COUNT(*) AS count FROM alerts")[0]["count"]
    sensors = query("SELECT COUNT(*) AS count FROM sensor_components")[0]["count"]

    return {
        "status": "ok",
        "frames": frames,
        "alerts": alerts,
        "registered_sensors": sensors
    }
