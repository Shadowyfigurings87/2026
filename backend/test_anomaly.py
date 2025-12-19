import sqlite3
from anomaly.engine import analyze_frame
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / "data" / "rf_archive.db"

def get_alerts():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT timestamp, alert_type, mac, severity, description FROM alerts ORDER BY timestamp DESC")
    rows = cursor.fetchall()
    conn.close()
    return rows

def test_analyze_frame():
    # 1. Unknown vendor
    frame1 = {
        "src_mac": "11:22:33:44:55:66",
        "classification": {},  # no vendor
        "sensor_id": "sensor-1",
        "sensor_component_role": "observatory",
        "frame_type": "control"
    }

    # 2. Very strong signal
    frame2 = {
        "src_mac": "AA:BB:CC:DD:EE:FF",
        "rssi_normalized": -15,  # triggers very_strong_signal
        "signal_quality": 0.8,
        "sensor_id": "sensor-2",
        "sensor_component_role": "observatory",
        "frame_type": "data"
    }

    # 3. Low signal quality
    frame3 = {
        "src_mac": "77:88:99:AA:BB:CC",
        "rssi_normalized": -40,
        "signal_quality": 0.2,  # triggers low_signal_quality
        "sensor_id": "sensor-3",
        "sensor_component_role": "observatory",
        "frame_type": "data"
    }

    # 4. Management storm
    frame4 = {
        "src_mac": "DD:EE:FF:00:11:22",
        "frame_type": "management",
        "activity_score": 5,  # triggers management_storm
        "sensor_id": "sensor-4",
        "sensor_component_role": "observatory"
    }

    # Run all frames through anomaly engine
    for f in [frame1, frame2, frame3, frame4]:
        analyze_frame(f)

    # Fetch alerts from DB
    alerts = get_alerts()
    print("Recent Alerts in DB:")
    for a in alerts[:10]:  # show last 10
        print(a)

if __name__ == "__main__":
    test_analyze_frame()
