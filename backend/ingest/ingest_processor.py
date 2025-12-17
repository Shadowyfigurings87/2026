# ingest/ingest_processor.py

import threading
import db
from datetime import datetime
from anomaly.engine import analyze_frame


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
    return min(score, 1.0) if score > 0 else None


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


def start_ingest_processor(ingest_queue):
    """
    Background thread:
    - consumes frames from ingest_queue
    - enriches them
    - inserts into DB via db.execute()
    - runs anomaly engine
    """

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

    def run():
        print("[INGEST] Processor online")

        while True:
            record = ingest_queue.get()

            # Identity lookup
            src_mac = record.get("src")
            dst_mac = record.get("dst")
            bssid   = record.get("bssid")

            src_info = identity_map.get((src_mac or "").lower())
            dst_info = identity_map.get((dst_mac or "").lower())
            bssid_info = identity_map.get((bssid or "").lower())

            src_role = src_info[1] if src_info else None
            dst_role = dst_info[1] if dst_info else None
            bssid_role = bssid_info[1] if bssid_info else None

            sensor_id = None
            component_role = None
            for info in (src_info, bssid_info, dst_info):
                if info:
                    sensor_id, component_role = info
                    break

            if sensor_id and component_role:
                update_heartbeat(sensor_id, src_mac, component_role)

            # Feature extraction
            frame_type = record.get("frame_type")
            activity_score = compute_activity_score(frame_type)

            rssi = record.get("rssi")
            try:
                rssi_value = int(rssi) if rssi is not None else None
            except Exception:
                rssi_value = None

            cal_offset = calibration_map.get((sensor_id, component_role), 0) if sensor_id else 0
            rssi_normalized = rssi_value + cal_offset if rssi_value is not None else None

            signal_quality = None
            if rssi_normalized is not None:
                signal_quality = (rssi_normalized + 100) / 100.0
                signal_quality = max(0.0, min(1.0, signal_quality))

            update_channel_metrics(record.get("channel"), sensor_id, component_role, activity_score)

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

            # Normalize channel_flags to string
            channel_flags = record.get("channel_flags")
            channel_flags = str(channel_flags) if channel_flags is not None else None

            # Insert frame
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
                channel_flags,
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
                db.execute(insert_stmt, values)
            except Exception as e:
                print(f"[INGEST] DB insert error: {e} | record={record}")

            # Rule-based anomaly engine
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
                print(f"[INGEST] Anomaly engine error: {e}")

    t = threading.Thread(target=run, daemon=True)
    t.start()
