# host/services/connect/worker.py

import time
from queue import Queue
from datetime import datetime

from host.logs.wrappers import log_ingest, log_rf
from host.services.metrics import (
    ingest_total,
    ingestion_queue_depth,
    rf_frames_total,
    rf_frame_processing_seconds,
)

# NEW imports for Arduino decoding + DB upsert
from host.services.arduino_decoder import decode_arduino_line
from host.services.db_writer import upsert_arduino_state

ingestion_queue: Queue = Queue()


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


def process_camera_frame(msg: dict):
    data = msg.get("data")
    if isinstance(data, (bytes, bytearray)):
        log_ingest("camera_frame_processed", metadata=msg)
    else:
        log_ingest("camera_frame_ignored_non_bytes", payload=msg)


def process_arduino_frame(msg: dict):
    """
    Handles:
      - Raw TEL: telemetry → decode + upsert arduino_state
      - ministry_metrics → log only
    """
    event = msg.get("event")

    # Metrics frames (from get_arduino_metrics)
    if event == "ministry_metrics":
        log_ingest("arduino_metrics", payload=msg)
        return

    # Raw telemetry frames
    raw_line = msg.get("raw") or msg.get("line") or msg.get("data")
    if not raw_line:
        log_ingest("arduino_frame_missing_raw", payload=msg)
        return

    decoded = decode_arduino_line(raw_line)
    if not decoded:
        log_ingest("arduino_frame_unparsed", raw=raw_line, payload=msg)
        return

    # Timestamp handling
    ts_iso = msg.get("timestamp") or datetime.utcnow().isoformat() + "Z"

    # Upsert into arduino_state table
    upsert_arduino_state(
        rpm=decoded.get("rpm", 0.0),
        throttle=decoded.get("throttle", 0.0),
        direction=decoded.get("direction", "UNKNOWN"),
        pwm=decoded.get("pwm", 0),
        ts=ts_iso,
        raw={
            "timestamp": ts_iso,
            "raw": raw_line,
            "decoded": decoded,
        },
    )

    log_ingest("arduino_frame_decoded", decoded=decoded)


def process_system_event(msg: dict):
    log_ingest("system_event", payload=msg)


def process_redrover_frame(msg: dict):
    log_ingest("redrover_frame", payload=msg)


def process_heartbeat(msg: dict):
    log_ingest("heartbeat_stub", payload=msg)


def process_watchdog(msg: dict):
    log_ingest("watchdog_stub", payload=msg)


def worker_loop():
    log_ingest("worker_loop_started")
    while True:
        msg = ingestion_queue.get()
        try:
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
