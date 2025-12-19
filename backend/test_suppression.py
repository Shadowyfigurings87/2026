import sqlite3
from anomaly.engine import analyze_frame
from pathlib import Path
from datetime import datetime, timedelta, timezone

DB_PATH = Path(__file__).resolve().parent / "data" / "rf_archive.db"

def clear_alerts(mac, alert_type):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM alerts WHERE mac = ? AND alert_type = ?", (mac, alert_type))
    conn.commit()
    conn.close()

def get_alerts(mac, alert_type):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT timestamp, alert_type, mac, severity, description
        FROM alerts
        WHERE mac = ? AND alert_type = ?
        ORDER BY timestamp DESC
    """, (mac, alert_type))
    rows = cursor.fetchall()
    conn.close()
    return rows

def test_suppression():
    mac = "AA:BB:CC:DD:EE:FF"
    alert_type = "very_strong_signal"

    clear_alerts(mac, alert_type)

    frame = {
        "src_mac": mac,
        "rssi_normalized": -15,
        "sensor_id": "sensor-test",
        "sensor_component_role": "observatory",
    }

    for _ in range(3):
        analyze_frame(frame)

    alerts = get_alerts(mac, alert_type)
    print("Alerts after rapid repeats:", alerts)
    assert len(alerts) == 1

    # Simulate passage of time
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    old_time = (datetime.now(timezone.utc) - timedelta(minutes=6)).isoformat()
    cursor.execute("UPDATE alerts SET timestamp = ? WHERE mac = ? AND alert_type = ?", (old_time, mac, alert_type))
    conn.commit()
    conn.close()

    analyze_frame(frame)

    alerts = get_alerts(mac, alert_type)
    print("Alerts after simulated time jump:", alerts)
    assert len(alerts) == 2

if __name__ == "__main__":
    test_suppression()
