# host/services/ingest.py

from host.logs.wrappers import log_ingest, log_rf
from host.services.frame_store import save_frame

import socket
import threading
import json
import time
import base64
from queue import Queue

from host.services.db_writer import write_queue, start_db_writer
from host.services.metrics import (
    ingest_total,
    ingestion_queue_depth,
    rf_frames_total,
    rf_frame_processing_seconds,
)

HOST = "0.0.0.0"
PORT = 5000

# ---------------------------------------------------------
# GLOBAL INGESTION QUEUE
# ---------------------------------------------------------
ingestion_queue = Queue()


# ---------------------------------------------------------
# PROCESSING FUNCTIONS
# ---------------------------------------------------------

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
        duration = time.perf_counter() - start
        rf_frame_processing_seconds.observe(duration)


def process_camera_frame(msg):
    log_ingest("camera_frame_processed", metadata=msg)


def process_arduino_frame(msg):
    log_ingest("arduino_frame_stub", payload=msg)


def process_heartbeat(msg):
    log_ingest("heartbeat_stub", payload=msg)


def process_watchdog(msg):
    log_ingest("watchdog_stub", payload=msg)


# ---------------------------------------------------------
# WORKER LOOP
# ---------------------------------------------------------

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

            elif ministry == "heartbeat":
                process_heartbeat(msg)

            elif ministry == "watchdog":
                process_watchdog(msg)

            else:
                log_ingest("ingest_unknown_ministry", ministry=ministry, payload=msg)

        finally:
            ingestion_queue_depth.set(ingestion_queue.qsize())
            ingestion_queue.task_done()


# ---------------------------------------------------------
# TCP INGESTION SERVER
# ---------------------------------------------------------

def handle_client(conn, addr):
    log_ingest("ingest_client_connected", addr=str(addr))

    try:
        with conn, conn.makefile("r") as f:
            for line in f:
                log_ingest("ingest_raw_line_received", raw=line)

                # Parse JSON safely
                try:
                    obj = json.loads(line)
                except Exception as e:
                    log_ingest("ingest_json_decode_error", error=str(e), raw=line)
                    continue

                # Normalize ministry/device naming
                # If a frame is present, treat it as picamera2
                ministry = (
                    obj.get("ministry")
                    or obj.get("device")
                    or ("picamera2" if "frame" in obj else "unknown")
                )

                # -------- STRIP JPEG BLOBS BEFORE QUEUE + DB --------
                if "frame" in obj:
                    frame_b64 = obj.pop("frame", None)
                    if frame_b64:
                        try:
                            binary = base64.b64decode(frame_b64)
                            path = save_frame(binary)
                            obj["frame_path"] = path
                        except Exception as e:
                            log_ingest("camera_frame_decode_error", error=str(e))

                # Queue insert (metadata only)
                ingest_total.inc()
                ingestion_queue.put(obj)
                ingestion_queue_depth.set(ingestion_queue.qsize())

                # DB insert (metadata only)
                try:
                    ts = obj.get("ts")
                    timestamp_utc = obj.get("timestamp")

                    write_queue.put((
                        "INSERT INTO telemetry_raw (timestamp_utc, ts, ministry, payload) VALUES (?, ?, ?, ?)",
                        (timestamp_utc, ts, ministry, json.dumps(obj))
                    ))

                except Exception as e:
                    log_ingest("ingest_db_enqueue_error", error=str(e), payload=obj)

    except Exception as e:
        log_ingest("ingest_client_handler_crashed", error=str(e), addr=str(addr))


def start_ingestion_server():
    log_ingest("ingestion_server_start")

    start_db_writer()
    threading.Thread(target=worker_loop, daemon=True).start()

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind((HOST, PORT))
    sock.listen(5)

    log_ingest("ingestion_server_listening", host=HOST, port=PORT)

    while True:
        conn, addr = sock.accept()
        threading.Thread(target=handle_client, args=(conn, addr), daemon=True).start()
