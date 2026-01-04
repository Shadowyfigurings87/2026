# api/anomaly_routes.py

from fastapi import APIRouter
import sqlite3
import os
from backend.utils.logging_config import log_event

router = APIRouter()

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


@router.get("/api/anomalies/recent")
def recent_anomalies():
    """
    Return recent ML anomalies from the anomalies table.
    """
    try:
        rows = query_db(
            """
            SELECT
                frame_timestamp AS timestamp,
                src_mac,
                channel,
                anomaly_score,
                anomaly_severity,
                anomaly_cluster,
                device_deviation,
                channel_deviation,
                frame_type,
                ssid,
                src_vendor,
                bssid_vendor
            FROM anomalies
            ORDER BY frame_timestamp DESC
            LIMIT 200
            """
        )

        return [
            {
                "timestamp": r["timestamp"],
                "src_mac": r["src_mac"],
                "channel": r["channel"],
                "anomaly_score": r["anomaly_score"] or 0.0,
                "anomaly_severity": r["anomaly_severity"] or "unknown",
                "anomaly_cluster": r["anomaly_cluster"] or "unclassified",
                "device_deviation": r["device_deviation"] or 0.0,
                "channel_deviation": r["channel_deviation"] or 0.0,
                "frame_type": r["frame_type"] or "unknown",
                "ssid": r["ssid"],
                "src_vendor": r["src_vendor"],
                "bssid_vendor": r["bssid_vendor"],
            }
            for r in rows
        ]

    except Exception as e:
        log_event("api", "ERROR", "recent_anomalies_failed", {"error": str(e)})
        return {"error": "failed_to_fetch"}
