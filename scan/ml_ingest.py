#!/usr/bin/env python3
import sys
import json
import sqlite3
from datetime import datetime

DB_PATH = "/home/zachariah/2026/scan/data/rf_archive.db"
BATCH_SIZE = 100

# -------------------------------------------------------------------
# DB setup and helpers
# -------------------------------------------------------------------

def connect_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    conn.execute("PRAGMA foreign_keys=ON;")
    conn.execute("PRAGMA busy_timeout=5000;")
    return conn

def log_event(cursor, status, message):
    cursor.execute(
        "INSERT INTO ingest_log (timestamp, status, message) VALUES (?, ?, ?)",
        (datetime.utcnow().isoformat(), status, message)
    )

def load_identity_map(cursor):
    """
    Returns:
        identity_map: mac_lower -> (sensor_id, role)
    """
    cursor.execute("SELECT sensor_id, mac, role FROM sensor_components")
    identity = {}
    for sensor_id, mac, role in cursor.fetchall():
        if mac:
            identity[mac.lower()] = (sensor_id, role)
    return identity

def load_calibration_map(cursor):
    """
    Returns:
        calibration_map: (sensor_id, role) -> offset
    """
    cursor.execute("SELECT sensor_id, component_role, offset FROM rssi_calibration")
    cal = {}
    for sensor_id, role, offset in cursor.fetchall():
        cal[(sensor_id, role)] = offset
    return cal

def update_heartbeat(cursor, sensor_id, mac, role):
    cursor.execute(
        """
        INSERT INTO sensor_status (sensor_id, last_seen, component_mac, component_role)
        VALUES (?, ?, ?, ?)
        """,
        (sensor_id, datetime.utcnow().isoformat(), mac, role),
    )

def update_channel_metrics(cursor, channel, sensor_id, role, activity_score):
    if channel is None:
        return
    cursor.execute(
        """
        INSERT INTO channel_metrics (timestamp, channel, sensor_id, component_role, activity_score)
        VALUES (?, ?, ?, ?, ?)
        """,
        (datetime.utcnow().isoformat(), channel, sensor_id, role, activity_score),
    )

def record_alert(cursor, alert_type, mac, sensor_id, role, severity, description):
    cursor.execute(
        """
        INSERT INTO alerts (timestamp, alert_type, mac, sensor_id, component_role, severity, description)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            datetime.utcnow().isoformat(),
            alert_type,
            mac,
            sensor_id,
            role,
            severity,
            description,
        ),
    )
    print(f"[ALERT] {alert_type.upper()} | {severity:.2f} | {description}", flush=True)

# -------------------------------------------------------------------
# Feature and scoring helpers
# -------------------------------------------------------------------

def compute_activity_score(frame_type):
    if frame_type == "management":
        return 3
    if frame_type == "data":
        return 2
    if frame_type == "control":
        return 1
    return 0

def compute_basic_anomaly_score(activity_score, signal_quality):
    """
    Very simple anomaly signal:
      - higher activity_score bumps it
      - low signal_quality bumps it
    Purely heuristic for now; future DAG/ML can replace this.
    """
    score = 0.0

    if activity_score is not None:
        if activity_score >= 3:
            score += 0.3
        elif activity_score == 2:
            score += 0.2

    if signal_quality is not None:
        if signal_quality < 0.3:
            score += 0.4
        elif signal_quality < 0.5:
            score += 0.2

    if score > 1.0:
        score = 1.0
    return score if score > 0 else None

# -------------------------------------------------------------------
# Main ingest loop
# -------------------------------------------------------------------

def main():
    conn = connect_db()
    cursor = conn.cursor()

    print("[+] ml_ingest.py Phase 14 — consolidated sovereign ingest engine", flush=True)
    log_event(cursor, "start", "Ingest script started (Phase 14)")

    identity_map = load_identity_map(cursor)
    calibration_map = load_calibration_map(cursor)

    insert_stmt = """
        INSERT INTO frames (
            timestamp, source, iface,
            frame_type, subtype, direction,
            src_mac, dst_mac, bssid, ssid,
            channel, rssi, rate, channel_freq, channel_flags,
            summary,
            src_role, dst_role, bssid_role,
            sensor_id, sensor_component_role,
            rssi_normalized, signal_quality, activity_score
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """

    batch_count = 0

    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue

        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            msg = f"JSON decode error: {line[:80]}"
            print(f"[!] {msg}", flush=True)
            log_event(cursor, "json_error", msg)
            continue

        # ------------------------------------------------------------------
        # Identity lookup
        # ------------------------------------------------------------------
        src_mac = record.get("src")
        dst_mac = record.get("dst")
        bssid   = record.get("bssid")

        src_info = identity_map.get((src_mac or "").lower())
        dst_info = identity_map.get((dst_mac or "").lower())
        bssid_info = identity_map.get((bssid or "").lower())

        src_role = src_info[1] if src_info else None
        dst_role = dst_info[1] if dst_info else None
        bssid_role = bssid_info[1] if bssid_info else None

        # Determine primary sensor origin: src > bssid > dst
        sensor_id = None
        component_role = None
        for info in (src_info, bssid_info, dst_info):
            if info:
                sensor_id, component_role = info
                break

        # Heartbeat update (only if we can attribute the frame)
        if sensor_id and component_role:
            update_heartbeat(cursor, sensor_id, src_mac, component_role)

        # ------------------------------------------------------------------
        # Feature extraction
        # ------------------------------------------------------------------
        frame_type = record.get("frame_type")
        activity_score = compute_activity_score(frame_type)

        rssi = record.get("rssi")
        cal_offset = 0
        if sensor_id and component_role:
            cal_offset = calibration_map.get((sensor_id, component_role), 0)

        if rssi is not None:
            try:
                rssi_value = int(rssi)
            except (TypeError, ValueError):
                rssi_value = None
        else:
            rssi_value = None

        rssi_normalized = rssi_value + cal_offset if rssi_value is not None else None

        signal_quality = None
        if rssi_normalized is not None:
            # simple mapping: -100 dBm -> 0.0, 0 dBm -> 1.0
            signal_quality = (rssi_normalized + 100) / 100.0
            if signal_quality < 0:
                signal_quality = 0.0
            if signal_quality > 1:
                signal_quality = 1.0

        # Channel metrics
        update_channel_metrics(cursor, record.get("channel"), sensor_id, component_role, activity_score)

        # Basic anomaly signal → alerts
        anomaly_score = compute_basic_anomaly_score(activity_score, signal_quality)
        if anomaly_score is not None and anomaly_score >= 0.6:
            record_alert(
                cursor,
                alert_type="rf_anomaly",
                mac=src_mac,
                sensor_id=sensor_id,
                role=component_role,
                severity=anomaly_score,
                description=f"Elevated anomaly score ({anomaly_score:.2f}) frame_type={frame_type}",
            )

        # ------------------------------------------------------------------
        # Insert frame
        # ------------------------------------------------------------------
        values = (
            record.get("timestamp"),
            record.get("source"),
            record.get("iface"),
            frame_type,
            record.get("subtype"),
            record.get("direction"),
            src_mac,
            dst_mac,
            bssid,
            record.get("ssid"),
            record.get("channel"),
            rssi_value,
            record.get("rate"),
            record.get("channel_freq"),
            record.get("channel_flags"),
            record.get("summary"),
            src_role,
            dst_role,
            bssid_role,
            sensor_id,
            component_role,
            rssi_normalized,
            signal_quality,
            activity_score,
        )

        try:
            cursor.execute(insert_stmt, values)
            batch_count += 1
        except Exception as e:
            msg = f"DB insert error: {str(e)}"
            print(f"[!] {msg}", flush=True)
            log_event(cursor, "db_error", msg)
            continue

        if batch_count >= BATCH_SIZE:
            conn.commit()
            print(f"[+] Committed batch of {BATCH_SIZE} frames", flush=True)
            batch_count = 0

    # Final commit
    if batch_count > 0:
        conn.commit()
        print(f"[+] Final commit of {batch_count} frames", flush=True)

    log_event(cursor, "stop", "Ingest script finished (Phase 14)")
    conn.commit()
    conn.close()

    print("[+] ml_ingest.py Phase 14 complete", flush=True)

if __name__ == "__main__":
    main()
