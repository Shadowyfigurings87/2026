# anomaly/engine.py

import db
from anomaly.rules import RULES
from anomaly.scorer import compute_severity
from utils.time import now_iso


def analyze_frame(frame: dict):
    """
    Run all anomaly rules on a frame dict (as stored in DB / from ingest).
    Insert alerts for each triggered rule.
    """
    triggered = []

    for rule in RULES:
        result = rule(frame)
        if result:
            triggered.append(result)

    for anomaly in triggered:
        severity = compute_severity(anomaly)
        insert_alert(frame, anomaly, severity)


def insert_alert(frame: dict, anomaly: dict, severity: float):
    sql = """
        INSERT INTO alerts (timestamp, alert_type, mac, sensor_id, component_role, severity, description)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """

    params = (
        now_iso(),
        anomaly["type"],
        anomaly.get("mac"),
        frame.get("sensor_id"),
        frame.get("sensor_component_role"),
        severity,
        anomaly["description"],
    )

    # This now enqueues the write instead of writing directly to SQLite.
    db.execute(sql, params)
