# host/services/connect/worker.py

import time
from queue import Queue
from datetime import datetime, timezone

from host.logs.wrappers import log_ingest, log_rf
from host.services.metrics import (
    ingest_total,
    ingestion_queue_depth,
    rf_frames_total,
    rf_frame_processing_seconds,
)

# Arduino DB upsert
from host.services.db_writer import upsert_arduino_state

ingestion_queue: Queue = Queue()


# ============================================================
# RF MINISTRY
# ============================================================

def process_rf_frame(msg: dict):
    start = time.perf_counter()
    try:
        rf_frames_total.inc()

        log_rf(
            "rf_frame_received",
            rssi=msg.get("rssi"),
            frame_type=msg.get("frame_type"),
            ssid=msg.get("ssid"),
            src=msg.get("src"),
            dst=msg.get("dst"),
            bssid=msg.get("bssid"),
            queue_pressure=msg.get("_queue_pressure"),
        )

    finally:
        rf_frame_processing_seconds.observe(time.perf_counter() - start)


# ============================================================
# CAMERA MINISTRY
# ============================================================

def process_camera_frame(msg: dict):
    data = msg.get("data")
    if isinstance(data, (bytes, bytearray)):
        log_ingest("camera_frame_processed", metadata=msg)
    else:
        log_ingest("camera_frame_ignored_non_bytes", payload=msg)


# ============================================================
# ARDUINO MINISTRY (JSON-first, ASCII fallback)
# ============================================================

def process_arduino_frame(msg: dict):
    """
    Unified Arduino telemetry handler.
    Supports BOTH:
      - JSON telemetry from Rover1
      - Legacy ASCII TEL: telemetry from Arduino
    """

    # -------------------------------------------------------
    # 1. JSON TELEMETRY (preferred)
    # -------------------------------------------------------
    if all(k in msg for k in ("rpm", "throttle", "direction", "pwm")):
        rpm = msg.get("rpm")
        throttle = msg.get("throttle")
        direction = msg.get("direction")
        pwm = msg.get("pwm")

        ts_iso = (
            msg.get("timestamp")
            or datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        )

        log_ingest("arduino_json_telemetry", payload=msg)

        upsert_arduino_state(
            rpm=rpm,
            throttle=throttle,
            direction=direction,
            pwm=pwm,
            ts=ts_iso,
            raw=msg,
        )
        return

    # -------------------------------------------------------
    # 2. ASCII TELEMETRY (legacy fallback)
    # -------------------------------------------------------

    raw_line = msg.get("raw") or msg.get("line") or msg.get("data")
    if not raw_line:
        log_ingest("arduino_frame_missing_raw", payload=msg)
        return

    if not raw_line.startswith("TEL"):
        log_ingest("arduino_frame_unparsed", raw=raw_line, payload=msg)
        return

    parts = raw_line.replace("TEL:", "").strip().split()

    parsed = {}
    for part in parts:
        if ":" not in part:
            continue

        key, value = part.split(":", 1)
        key = key.strip().lower()
        value = value.strip()

        if key == "rpm":
            try:
                parsed["rpm"] = float(value)
            except Exception:
                parsed["rpm"] = None

        elif key in ("thr", "throttle"):
            try:
                parsed["throttle"] = float(value)
            except Exception:
                parsed["throttle"] = None

        elif key == "dir":
            parsed["direction"] = value.upper()

        elif key == "pwm":
            try:
                parsed["pwm"] = float(value)
            except Exception:
                parsed["pwm"] = None

    parsed.setdefault("rpm", None)
    parsed.setdefault("throttle", None)
    parsed.setdefault("direction", None)
    parsed.setdefault("pwm", None)

    ts_iso = (
        msg.get("timestamp")
        or datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    )

    log_ingest("arduino_frame_parsed_ascii", payload={
        "raw": raw_line,
        "parsed": parsed,
    })

    upsert_arduino_state(
        rpm=parsed["rpm"],
        throttle=parsed["throttle"],
        direction=parsed["direction"],
        pwm=parsed["pwm"],
        ts=ts_iso,
        raw={
            "timestamp": ts_iso,
            "raw": raw_line,
            "decoded": parsed,
        },
    )


# ============================================================
# SYSTEM / REDROVER / HEARTBEAT / WATCHDOG
# ============================================================

def process_system_event(msg: dict):
    log_ingest("system_event", payload=msg)


def process_redrover_frame(msg: dict):
    log_ingest("redrover_frame", payload=msg)


def process_heartbeat(msg: dict):
    log_ingest("heartbeat_event", payload=msg)


def process_watchdog(msg: dict):
    log_ingest("watchdog_event", payload=msg)


# ============================================================
# WORKER LOOP
# ============================================================

def worker_loop():
    log_ingest("worker_loop_started")

    while True:
        msg = ingestion_queue.get()
        try:
            ingest_total.inc()

            ministry = msg.get("ministry")

            if ministry == "alfa":
                process_rf_frame(msg)

            elif ministry == "picamera2":
                process_camera_frame(msg)

            elif ministry == "arduino":
                process_arduino_frame(msg)

            elif ministry == "system":
                process_system_event(msg)

            elif ministry == "redrover":
                process_redrover_frame(msg)

            elif ministry == "heartbeat":
                process_heartbeat(msg)

            elif ministry == "watchdog":
                process_watchdog(msg)

            else:
                log_ingest("ingest_unknown_ministry", ministry=ministry, payload=msg)

        finally:
            ingestion_queue_depth.set(ingestion_queue.qsize())
            ingestion_queue.task_done()
