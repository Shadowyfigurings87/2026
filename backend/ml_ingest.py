#!/usr/bin/env python3
import sys
import json
from datetime import datetime

import db
from anomaly.engine import analyze_frame


# -------------------------------------------------------------------
# Helpers for ingest logging (queued writes)
# -------------------------------------------------------------------

def log_event(status, message):
    sql = """
        INSERT INTO ingest_log (timestamp, status, message)
        VALUES (?, ?, ?)
    """
    params = (datetime.utcnow().isoformat(), status, message)
    db.execute(sql, params)


# -------------------------------------------------------------------
# Identity + calibration maps (loaded via db.query)
# -------------------------------------------------------------------

def load_identity_map():
    rows = db.query("SELECT sensor_id, mac, role FROM sensor_components")
    identity = {}
    for row in rows:
        mac = row["mac"]
        if mac:
            identity[mac.lower()] = (row["sensor_id"], row["role"])
    return identity


def load_calibration_map():
    rows = db.query("SELECT sensor_id, component_role, offset FROM rssi_calibration")
    cal = {}
    for row in rows:
        cal[(row["sensor_id"], row["component_role"])] = row["offset"]
    return cal


# -------------------------------------------------------------------
# Queued write helpers
# -------------------------------------------------------------------

def update_heartbeat(sensor_id, mac, role):
    sql = """
        INSERT INTO sensor_status (sensor_id, last_seen, component_mac, component_role)
        VALUES (?, ?, ?, ?)
    """
    params = (sensor_id, datetime.utcnow().isoformat(), mac, role)
    db.execute(sql, params)


def update_channel_metrics(channel, sensor_id, role, activity_score):
    if channel is None:
        return
    sql = """
        INSERT INTO channel_metrics (timestamp, channel, sensor_id, component_role, activity_score)
        VALUES (?, ?, ?, ?, ?)
    """
    params = (
        datetime.utcnow().isoformat(),
        channel,
        sensor_id,
        role,
        activity_score,
    )
    db.execute(sql, params)


def record_alert(alert_type, mac, sensor_id, role, severity, description):
    sql = """
        INSERT INTO alerts (timestamp, alert_type, mac, sensor_id, component_role, severity, description)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """
    params = (
        datetime.utcnow().isoformat(),
        alert_type,
        mac,
        sensor_id,
        role,
        severity,
        description,
    )
    db.execute(sql, params)
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
# Main ingest loop (now queue‑based)
# -------------------------------------------------------------------

def main():
    print("[+] ml_ingest.py Phase 15 — sovereign queue‑based ingest engine", flush=True)
    log_event("start", "Ingest script started (Phase 15)")

    # Load identity + calibration maps via db.query()
    identity_map = load_identity_map()
    calibration_map = load_calibration_map()

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

    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue

        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            msg = f"JSON decode error: {line[:80]}"
            print(f"[!] {msg}", flush=True)
            log_event("json_error", msg)
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

        # Determine primary sensor origin
        sensor_id = None
        component_role = None
        for info in (src_info, bssid_info, dst_info):
            if info:
                sensor_id, component_role = info
                break

        # Heartbeat
        if sensor_id and component_role:
            update_heartbeat(sensor_id, src_mac, component_role)

        # ------------------------------------------------------------------
        # Feature extraction
        # ------------------------------------------------------------------
        frame_type = record.get("frame_type")
        activity_score = compute_activity_score(frame_type)

        rssi = record.get("rssi")
        cal_offset = calibration_map.get((sensor_id, component_role), 0) if sensor_id else 0

        try:
            rssi_value = int(rssi) if rssi is not None else None
        except (TypeError, ValueError):
            rssi_value = None

        rssi_normalized = rssi_value + cal_offset if rssi_value is not None else None

        signal_quality = None
        if rssi_normalized is not None:
            signal_quality = (rssi_normalized + 100) / 100.0
            signal_quality = max(0.0, min(1.0, signal_quality))

        # Channel metrics
        update_channel_metrics(record.get("channel"), sensor_id, component_role, activity_score)

        # Basic anomaly signal
        anomaly_score = compute_basic_anomaly_score(activity_score, signal_quality)
        if anomaly_score is not None and anomaly_score >= 0.6:
            record_alert(
                "rf_anomaly",
                src_mac,
                sensor_id,
                component_role,
                anomaly_score,
                f"Elevated anomaly score ({anomaly_score:.2f}) frame_type={frame_type}",
            )

        # ------------------------------------------------------------------
        # Insert frame (queued write)
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

        db.execute(insert_stmt, values)

        # ------------------------------------------------------------------
        # Rule‑based anomaly engine
        # ------------------------------------------------------------------
        frame_dict = {
            "timestamp": values[0],
            "source": values[1],
            "iface": values[2],
            "frame_type": values[3],
            "subtype": values[4],
            "direction": values[5],
            "src_mac": values[6],
            "dst_mac": values[7],
            "bssid": values[8],
            "ssid": values[9],
            "channel": values[10],
            "rssi": values[11],
            "rate": values[12],
            "channel_freq": values[13],
            "channel_flags": values[14],
            "summary": values[15],
            "src_role": values[16],
            "dst_role": values[17],
            "bssid_role": values[18],
            "sensor_id": values[19],
            "sensor_component_role": values[20],
            "rssi_normalized": values[21],
            "signal_quality": values[22],
            "activity_score": values[23],
        }

        try:
            analyze_frame(frame_dict)
        except Exception as e:
            msg = f"Anomaly engine error: {str(e)}"
            print(f"[!] {msg}", flush=True)
            log_event("anomaly_error", msg)

    # End of ingest
    log_event("stop", "Ingest script finished (Phase 15)")
    print("[+] ml_ingest.py Phase 15 complete", flush=True)


if __name__ == "__main__":
    main()
