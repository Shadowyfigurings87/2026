# api/channel_routes.py

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


@router.get("/api/channels/top_deviation")
def top_channels_deviation():
    """
    Channels ranked by maximum observed channel_deviation.
    """
    try:
        rows = query_db(
            """
            SELECT
                channel,
                MAX(channel_deviation) AS max_dev,
                COUNT(*) AS samples
            FROM anomalies
            WHERE channel IS NOT NULL
            GROUP BY channel
            HAVING samples >= 5
            ORDER BY max_dev DESC
            LIMIT 50
            """
        )

        return [
            {
                "channel": r["channel"],
                "max_deviation": r["max_dev"] or 0.0,
                "samples": r["samples"] or 0,
            }
            for r in rows
        ]

    except Exception as e:
        log_event("api", "ERROR", "top_channels_deviation_failed", {"error": str(e)})
        return {"error": "failed_to_fetch"}


@router.get("/api/channel/{ch}/timeline")
def channel_timeline(ch: int):
    """
    Timeline of anomalies for a specific channel.
    """
    try:
        rows = query_db(
            """
            SELECT
                frame_timestamp AS timestamp,
                src_mac,
                frame_type,
                anomaly_score,
                anomaly_severity,
                anomaly_cluster,
                device_deviation,
                channel_deviation
            FROM anomalies
            WHERE channel = ?
            ORDER BY frame_timestamp DESC
            LIMIT 200
            """,
            (ch,),
        )

        return [
            {
                "timestamp": r["timestamp"],
                "src_mac": r["src_mac"],
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
        log_event("api", "ERROR", "channel_timeline_failed", {"error": str(e)})
        return {"error": "failed_to_fetch"}
