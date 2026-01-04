# api/device_routes.py

from fastapi import APIRouter
import sqlite3
import os

from backend.utils.logging_config import log_event

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


@router.get("/api/devices/top_deviation")
def top_devices_deviation():
    """
    Devices ranked by maximum observed device_deviation.
    """
    try:
        rows = query_db(
            """
            SELECT
                src_mac,
                MAX(device_deviation) AS max_dev,
                COUNT(*) AS samples
            FROM anomalies
            WHERE src_mac IS NOT NULL
            GROUP BY src_mac
            HAVING samples >= 5
            ORDER BY max_dev DESC
            LIMIT 50
            """
        )

        return [
            {
                "src_mac": r["src_mac"],
                "max_deviation": r["max_dev"] or 0.0,
                "samples": r["samples"] or 0,
            }
            for r in rows
        ]

    except Exception as e:
        log_event("api", "ERROR", "top_devices_deviation_failed", {"error": str(e)})
        return {"error": "failed_to_fetch"}


@router.get("/api/device/{mac}/timeline")
def device_timeline(mac: str):
    """
    Timeline of anomalies for a specific device.
    """
    try:
        rows = query_db(
            """
            SELECT
                frame_timestamp AS timestamp,
                channel,
                frame_type,
                anomaly_score,
                anomaly_severity,
                anomaly_cluster,
                device_deviation,
                channel_deviation
            FROM anomalies
            WHERE src_mac = ?
            ORDER BY frame_timestamp DESC
            LIMIT 200
            """,
            (mac.lower(),),
        )

        return [
            {
                "timestamp": r["timestamp"],
                "channel": r["channel"],
                "frame_type": r["frame_type"],
                "anomaly_score": r["anomaly_score"] or 0.0,
                "anomaly_severity": r["anomaly_severity"] or "unknown",
                "anomaly_cluster": r["anomaly_cluster"] or "unclassified",
                "device_deviation": r["device_deviation"] or 0.0,
                "channel_deviation": r["channel_deviation"] or 0.0,
            }
            for r in rows
        ]

    except Exception as e:
        log_event("api", "ERROR", "device_timeline_failed", {"error": str(e)})
        return {"error": "failed_to_fetch"}
