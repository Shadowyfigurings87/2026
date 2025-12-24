# api/threat_routes.py

from fastapi import APIRouter
import sqlite3
import os
from utils.logging_config import log_event

router = APIRouter(prefix="/dashboard")

DB_PATH = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    "data",
    "rf_archive.db"
)


def query_db(sql, params=()):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        cur = conn.cursor()
        cur.execute(sql, params)
        return cur.fetchall()
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Threat Summary
# ---------------------------------------------------------------------------

@router.get("/api/threat/summary")
def threat_summary():
    """
    Overall threat summary:
      - recent critical anomalies
      - top SSIDs
      - top vendors
    """
    try:
        crit = query_db(
            """
            SELECT COUNT(*) AS c
            FROM anomalies
            WHERE anomaly_severity = 'critical'
              AND frame_timestamp >= datetime('now', '-10 minutes')
            """
        )[0]["c"]

        by_ssid = query_db(
            """
            SELECT ssid, COUNT(*) AS c
            FROM anomalies
            WHERE ssid IS NOT NULL
            GROUP BY ssid
            ORDER BY c DESC
            LIMIT 10
            """
        )

        by_vendor = query_db(
            """
            SELECT src_vendor, COUNT(*) AS c
            FROM anomalies
            WHERE src_vendor IS NOT NULL
            GROUP BY src_vendor
            ORDER BY c DESC
            LIMIT 10
            """
        )

        return {
            "critical_last_10m": crit,
            "top_ssids": [{"ssid": r["ssid"], "count": r["c"]} for r in by_ssid],
            "top_vendors": [{"vendor": r["src_vendor"], "count": r["c"]} for r in by_vendor],
        }

    except Exception as e:
        log_event("api", "ERROR", "threat_summary_failed", {"error": str(e)})
        return {"error": "failed_to_fetch"}


# ---------------------------------------------------------------------------
# Rogue AP Alerts
# ---------------------------------------------------------------------------

@router.get("/api/threat/rogue_aps")
def rogue_aps():
    """
    List suspected rogue APs from alerts table.
    """
    try:
        rows = query_db(
            """
            SELECT timestamp, mac, sensor_id, component_role, severity, description
            FROM alerts
            WHERE alert_type = 'rogue_ap_suspected'
            ORDER BY timestamp DESC
            LIMIT 100
            """
        )

        return [
            {
                "timestamp": r["timestamp"],
                "bssid": r["mac"],
                "sensor_id": r["sensor_id"],
                "role": r["component_role"],
                "severity": r["severity"],
                "description": r["description"],
            }
            for r in rows
        ]

    except Exception as e:
        log_event("api", "ERROR", "rogue_aps_failed", {"error": str(e)})
        return {"error": "failed_to_fetch"}


# ---------------------------------------------------------------------------
# Spoofing Alerts
# ---------------------------------------------------------------------------

@router.get("/api/threat/spoofing")
def spoofing_events():
    try:
        rows = query_db(
            """
            SELECT timestamp, mac, sensor_id, component_role, severity, description
            FROM alerts
            WHERE alert_type = 'mac_spoofing_suspected'
            ORDER BY timestamp DESC
            LIMIT 100
            """
        )

        return [
            {
                "timestamp": r["timestamp"],
                "mac": r["mac"],
                "sensor_id": r["sensor_id"],
                "role": r["component_role"],
                "severity": r["severity"],
                "description": r["description"],
            }
            for r in rows
        ]

    except Exception as e:
        log_event("api", "ERROR", "spoofing_events_failed", {"error": str(e)})
        return {"error": "failed_to_fetch"}


# ---------------------------------------------------------------------------
# Jamming Alerts
# ---------------------------------------------------------------------------

@router.get("/api/threat/jamming")
def jamming_events():
    try:
        rows = query_db(
            """
            SELECT timestamp, mac, sensor_id, component_role, severity, description
            FROM alerts
            WHERE alert_type = 'jamming_suspected'
            ORDER BY timestamp DESC
            LIMIT 100
            """
        )

        return [
            {
                "timestamp": r["timestamp"],
                "sensor_id": r["sensor_id"],
                "role": r["component_role"],
                "severity": r["severity"],
                "description": r["description"],
            }
            for r in rows
        ]

    except Exception as e:
        log_event("api", "ERROR", "jamming_events_failed", {"error": str(e)})
        return {"error": "failed_to_fetch"}


# ---------------------------------------------------------------------------
# All Rule-Based Alerts
# ---------------------------------------------------------------------------

@router.get("/api/threat/rule_alerts")
def rule_alerts():
    rows = query_db(
        """
        SELECT timestamp, alert_type, mac, severity, description
        FROM alerts
        WHERE alert_type IN (
            'rogue_ap_suspected',
            'mac_spoofing_suspected',
            'jamming_suspected',
            'unknown_vendor',
            'very_strong_signal',
            'low_signal_quality',
            'management_storm'
        )
        ORDER BY timestamp DESC
        LIMIT 200
        """
    )

    return [dict(r) for r in rows]
