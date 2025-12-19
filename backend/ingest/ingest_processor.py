# ingest/ingest_processor.py

import threading
import os
import sqlite3
from datetime import datetime

from anomaly.engine import analyze_frame
from utils.logging import log_event  # unified logger


# --- DB helpers -------------------------------------------------------------

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "rf_archive.db")


def query_db(sql, params=()):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute(sql, params)
        rows = cursor.fetchall()
        return rows
    finally:
        conn.close()


def execute_db(sql, params=()):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute(sql, params)
        conn.commit()
    finally:
        conn.close()


# --- Identity & calibration maps -------------------------------------------

def load_identity_map():
    """
    Load sensor_components into a MAC → {sensor_id, role} map.
    """
    rows = query_db("SELECT sensor_id, mac, role FROM sensor_components")

    identity_map = {}
    for sensor_id, mac, role in rows:
        if mac:
            identity_map[mac.lower()] = {
                "sensor_id": sensor_id,
                "role": role,
            }

    return identity_map


def load_calibration_map():
    """
    Load RSSI calibration offsets as (sensor_id, component_role) → offset.
    """
    rows = query_db("SELECT sensor_id, component_role, offset FROM rssi_calibration")

    calibration_map = {}
    for sensor_id, component_role, offset in rows:
        calibration_map[(sensor_id, component_role)] = offset

    return calibration_map


# --- Scoring helpers --------------------------------------------------------

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


# --- DB update helpers ------------------------------------------------------

def update_heartbeat(sensor_id, mac, role):
    sql = """
        INSERT INTO sensor_status (sensor_id, last_seen, component_mac, component_role)
        VALUES (?, ?, ?, ?)
    """
    params = (sensor_id, datetime.utcnow().isoformat(), mac, role)
    execute_db(sql, params)


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
    execute_db(sql, params)


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
    execute_db(sql, params)


# --- Main ingest processor --------------------------------------------------

def start_ingest_processor(ingest_queue):
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
        log_event("ingest_processor", "INFO", "processor_online")

        while True:
            record = ingest_queue.get()

            # --- Identity lookup -------------------------------------------
            src_mac = record.get("src")
            dst_mac = record.get("dst")
            bssid   = record.get("bssid")

            src_info = identity_map.get((src_mac or "").lower())
            dst_info = identity_map.get((dst_mac or "").lower())
            bssid_info = identity_map.get((bssid or "").lower())

            src_role = src_info["role"] if src_info else None
            dst_role = dst_info["role"] if dst_info else None
            bssid_role = bssid_info["role"] if bssid_info else None

            sensor_id = None
            component_role = None
            for info in (src_info, bssid_info, dst_info):
                if info:
                    sensor_id = info["sensor_id"]
                    component_role = info["role"]
                    break

            if sensor_id and component_role and src_mac:
                update_heartbeat(sensor_id, src_mac, component_role)

            # --- Feature extraction ----------------------------------------
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

            log_event("ingest_processor", "INFO", "frame_received", {
                "src": src_mac,
                "dst": dst_mac,
                "type": frame_type
            })

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

            log_event("ingest_processor", "INFO", "anomaly_score", {
                "score": anomaly_score,
                "frame_type": frame_type
            })

            # Normalize channel_flags
            channel_flags = record.get("channel_flags")
            channel_flags = str(channel_flags) if channel_flags is not None else None

            log_event("ingest_processor", "INFO", "frame_normalized", {
                "rssi": rssi_value,
                "rssi_normalized": rssi_normalized,
                "signal_quality": signal_quality
            })

            # --- Insert frame into DB --------------------------------------
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
                execute_db(insert_stmt, values)
            except Exception as e:
                log_event("ingest_processor", "ERROR", "db_insert_error", {
                    "error": str(e),
                    "record": record
                })

            # --- Rule-based anomaly engine ---------------------------------
            try:
                analyze_frame({
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
                })
            except Exception as e:
                log_event("ingest_processor", "ERROR", "anomaly_engine_error", {
                    "error": str(e)
                })

    threading.Thread(target=run, daemon=True).start()
