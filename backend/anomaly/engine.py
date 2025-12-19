from pathlib import Path
from datetime import datetime, timedelta, timezone
import sqlite3
import yaml
from anomaly.rules import RULES
from anomaly.scorer import compute_severity
from utils.time import now_iso

# Load config
CONFIG_PATH = Path(__file__).resolve().parent.parent / "data" / "config.yaml"
config = {}
if CONFIG_PATH.exists():
    with open(CONFIG_PATH, "r") as f:
        config = yaml.safe_load(f)

DB_PATH = config.get("database", {}).get(
    "path",
    str(Path(__file__).resolve().parent.parent / "data" / "rf_archive.db")
)

SUPPRESSION_WINDOW = timedelta(
    minutes=config.get("suppression", {}).get("window_minutes", 5)
)

def analyze_frame(frame: dict):
    triggered = []
    for rule in RULES:
        result = rule(frame)
        if result:
            triggered.append(result)

    for anomaly in triggered:
        severity = compute_severity(anomaly)
        insert_alert(frame, anomaly, severity)

def insert_alert(frame: dict, anomaly: dict, severity: float):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT timestamp FROM alerts
            WHERE alert_type = ? AND mac = ?
            ORDER BY timestamp DESC LIMIT 1
        """, (anomaly.get("type"), anomaly.get("mac")))
        row = cursor.fetchone()
        if row:
            last_time = datetime.fromisoformat(row[0])
            now = datetime.now(timezone.utc)
            if now - last_time < SUPPRESSION_WINDOW:
                return  # skip duplicate

        sql = """
            INSERT INTO alerts (timestamp, alert_type, mac, sensor_id, component_role, severity, description)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """
        params = (
            now_iso(),
            anomaly.get("type", "unknown"),
            anomaly.get("mac"),
            frame.get("sensor_id"),
            frame.get("sensor_component_role"),
            severity,
            anomaly.get("description", "no description"),
        )
        cursor.execute(sql, params)
        conn.commit()
    finally:
        conn.close()
