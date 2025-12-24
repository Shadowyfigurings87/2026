# services/ingest_processor.py

from utils.mac import lookup_vendor

import threading
import os
import sqlite3
from datetime import datetime

from services.anomaly.engine import analyze_frame, config as anomaly_config
from services.anomaly_engine import engine as ml_anomaly_engine
from services.severity import classify_severity
from services.clustering_engine import engine as cluster_engine
from services.device_model import engine as device_engine
from services.channel_model import engine as channel_engine
from services.alert_engine import engine as alert_engine

from utils.logging_config import log_event
import services.observatory as observatory


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
    rows = query_db("SELECT sensor_id, component_role, offset FROM rssi_calibration")
    calibration_map = {}
    for sensor_id, component_role, offset in rows:
        calibration_map[(sensor_id, component_role)] = offset
    return calibration_map


# --- ROVER DB INSERTS -------------------------------------------------------

def insert_rover_telemetry(ts, rover, source, data):
    sql = """
        INSERT INTO rover_telemetry (ts, rover, source, data)
        VALUES (?, ?, ?, json(?))
    """
    execute_db(sql, (ts, rover, source, json.dumps(data)))


def insert_rover_command_ack(ts, rover, command_id, status, raw):
    sql = """
        INSERT INTO rover_command_ack (ts, rover, command_id, status, raw)
        VALUES (?, ?, ?, ?, json(?))
    """
    execute_db(sql, (ts, rover, command_id, status, json.dumps(raw)))


# --- Scoring helpers --------------------------------------------------------

def compute_activity_score(frame_type):
    if frame_type == "management":
        return 3
    if frame_type == "data":
        return 2
    if frame_type == "control":
        return 1
    return 0


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


# --- MAIN INGEST PROCESSOR --------------------------------------------------

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
        log_event("ingest_processor", "INFO", "processor_online", {})

        while True:
            record = ingest_queue.get()

            # ------------------------------------------------------------------
            # ---------------------- ROVER TELEMETRY ---------------------------
            # ------------------------------------------------------------------
            kind = record.get("kind")

            if kind == "telemetry":
                ts = record.get("ts")
                rover = record.get("rover", "unknown")
                source = record.get("source", "unknown")
                data = record.get("data", {})

                insert_rover_telemetry(ts, rover, source, data)

                log_event("ingest_processor", "INFO", "rover_telemetry_ingested", {
                    "rover": rover,
                    "source": source
                })

                continue

            # ------------------------------------------------------------------
            # ---------------------- ROVER COMMAND ACK -------------------------
            # ------------------------------------------------------------------
            if kind == "command_ack":
                ts = record.get("ts")
                rover = record.get("rover", "Rover1")
                command_id = record.get("command_id")
                status = record.get("status", "unknown")

                insert_rover_command_ack(ts, rover, command_id, status, record)

                log_event("ingest_processor", "INFO", "rover_command_ack_ingested", {
                    "rover": rover,
                    "command_id": command_id,
                    "status": status
                })

                continue

            # ------------------------------------------------------------------
            # ---------------------- RF FRAME (DEFAULT) ------------------------
            # ------------------------------------------------------------------

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

            src_vendor = lookup_vendor(src_mac) if src_mac else None
            bssid_vendor = lookup_vendor(bssid) if bssid else None

            update_channel_metrics(record.get("channel"), sensor_id, component_role, activity_score)

            log_event("ingest_processor", "INFO", "frame_received", {
                "src": src_mac,
                "dst": dst_mac,
                "type": frame_type,
            })

            channel_flags = record.get("channel_flags")
            channel_flags = str(channel_flags) if channel_flags is not None else None

            log_event("ingest_processor", "INFO", "frame_normalized", {
                "rssi": rssi_value,
                "rssi_normalized": rssi_normalized,
                "signal_quality": signal_quality,
            })

            # --- Send basic frame metrics to observatory -------------------
            observatory.update_metrics({
                "timestamp": record.get("timestamp"),
                "src": src_mac,
                "dst": dst_mac,
                "frame_type": frame_type,
                "subtype": record.get("subtype"),
                "rssi": rssi_value,
                "signal_quality": signal_quality,
            })

            # ----------------------------------------------------------------
            # ---------------------- ML ENRICHMENT ---------------------------
            # ----------------------------------------------------------------

            ml_frame = {
                "timestamp": record.get("timestamp"),
                "source": record.get("source"),
                "iface": record.get("iface"),
                "frame_type": frame_type,
                "subtype": record.get("subtype"),
                "direction": record.get("direction"),
                "src": src_mac,
                "dst": dst_mac,
                "bssid": bssid,
                "ssid": record.get("ssid"),
                "channel": record.get("channel"),
                "rssi": rssi_value,
                "rate": record.get("rate"),
                "channel_freq": record.get("channel_freq"),
                "channel_flags": channel_flags,
                "summary": record.get("summary"),
                "src_role": src_role,
                "dst_role": dst_role,
                "bssid_role": bssid_role,
                "sensor_id": sensor_id,
                "sensor_component_role": component_role,
                "rssi_normalized": rssi_normalized,
                "signal_quality": signal_quality,
                "activity_score": activity_score,
                "src_vendor": src_vendor,
                "bssid_vendor": bssid_vendor,
            }

            # 1. ML anomaly score
            anomaly_score = ml_anomaly_engine.score_frame(ml_frame) or 0.0
            ml_frame["anomaly_score"] = anomaly_score

            # 2. Severity classification
            anomaly_severity = classify_severity(anomaly_score)
            ml_frame["anomaly_severity"] = anomaly_severity

            # 3. Device deviation
            device_dev = device_engine.update_and_score(ml_frame) or 0.0
            ml_frame["device_deviation"] = device_dev

            # 4. Channel deviation
            channel_dev = channel_engine.update_and_score(ml_frame) or 0.0
            ml_frame["channel_deviation"] = channel_dev

            # 5. Clustering
            try:
                features = ml_anomaly_engine._extract_features(ml_frame)
            except Exception:
                features = None
            cluster_label = cluster_engine.assign_cluster(features) if features is not None else None
            ml_frame["anomaly_cluster"] = cluster_label or "unclassified"

            # 6. Observatory anomaly score
            observatory.update_anomaly_score(anomaly_score, frame_type)

            # 7. Alerting
            should_alert = (
                anomaly_severity == "critical"
                or device_dev > 0.8
                or channel_dev > 0.8
            )

            if should_alert:
                description = (
                    f"ML anomaly detected: severity={anomaly_severity}, "
                    f"score={anomaly_score:.3f}, "
                    f"device_deviation={device_dev:.3f}, "
                    f"channel_deviation={channel_dev:.3f}, "
                    f"cluster={ml_frame['anomaly_cluster']}, "
                    f"frame_type={frame_type}"
                )
                record_alert(
                    alert_type="rf_ml_anomaly",
                    mac=src_mac,
                    sensor_id=sensor_id,
                    role=component_role,
                    severity=anomaly_severity,
                    description=description,
                )

                log_event("ingest_processor", "ALERT", "ml_anomaly_detected", {
                    "severity": anomaly_severity,
                    "score": anomaly_score,
                    "device_deviation": device_dev,
                    "channel_deviation": channel_dev,
                    "cluster": ml_frame["anomaly_cluster"],
                    "src": src_mac,
                    "channel": record.get("channel"),
                })

                alert_engine.send_alert(ml_frame)

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
                    "record": record,
                })

            # --- Rule-based anomaly engine (single, enriched call) ---------
            try:
                analyze_frame(
                    {
                        **ml_frame,
                        "anomaly_score": anomaly_score,
                        "anomaly_severity": anomaly_severity,
                        "device_deviation": device_dev,
                        "channel_deviation": channel_dev,
                    },
                    identity_map,
                    anomaly_config,
                )
            except Exception as e:
                log_event("ingest_processor", "ERROR", "anomaly_engine_error", {
                    "error": str(e),
                })

    threading.Thread(target=run, daemon=True).start()
