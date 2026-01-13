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
# MJPEG STATE (DISK-FIRST + LIVE-READY)
# ---------------------------------------------------------
latest_frame_bytes = None
latest_frame_timestamp = None

# Save every Nth frame
MJPEG_SAVE_EVERY_N = 5

# Counters
mjpeg_clients = 0
mjpeg_frames_total = 0
mjpeg_bytes_total = 0


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
# JSON TELEMETRY HANDLER
# ---------------------------------------------------------

def handle_json_client(conn, addr):
    log_ingest("ingest_json_client_connected", addr=str(addr))

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
        log_ingest("ingest_json_client_handler_crashed", error=str(e), addr=str(addr))


# ---------------------------------------------------------
# MJPEG STREAM HANDLER (DISK-FIRST + LIVE-READY)
# ---------------------------------------------------------

def _update_latest_frame(jpeg_bytes: bytes):
    global latest_frame_bytes, latest_frame_timestamp
    latest_frame_bytes = jpeg_bytes
    latest_frame_timestamp = time.time()


def handle_mjpeg_client(conn, addr):
    global mjpeg_clients, mjpeg_frames_total, mjpeg_bytes_total

    mjpeg_clients += 1
    log_ingest("mjpeg_client_connected", addr=str(addr), active_clients=mjpeg_clients)

    frame_counter = 0

    try:
        f = conn.makefile("rb")

        while True:
            # Expect boundary line: --frame\r\n
            boundary = f.readline()
            if not boundary:
                break

            if not boundary.startswith(b"--frame"):
                log_ingest("mjpeg_unexpected_boundary", boundary=boundary[:64])
                continue

            # Read headers until blank line
            headers = {}
            while True:
                line = f.readline()
                if not line or line in (b"\r\n", b"\n"):
                    break
                try:
                    key, value = line.decode("utf-8", errors="ignore").split(":", 1)
                    headers[key.strip().lower()] = value.strip()
                except ValueError:
                    continue

            content_length = headers.get("content-length")
            if content_length is None:
                log_ingest("mjpeg_missing_content_length", headers=headers)
                break

            try:
                length = int(content_length)
            except ValueError:
                log_ingest("mjpeg_invalid_content_length", value=content_length)
                break

            # Read JPEG payload
            jpeg_bytes = f.read(length)
            if not jpeg_bytes or len(jpeg_bytes) < length:
                log_ingest("mjpeg_incomplete_frame", expected=length, got=len(jpeg_bytes or b""))
                break

            mjpeg_frames_total += 1
            mjpeg_bytes_total += len(jpeg_bytes)
            frame_counter += 1

            # Update in-memory latest frame for live streaming
            _update_latest_frame(jpeg_bytes)

            # Save every Nth frame
            if frame_counter % MJPEG_SAVE_EVERY_N == 0:
                try:
                    path = save_frame(jpeg_bytes)
                    log_ingest(
                        "mjpeg_frame_saved",
                        path=path,
                        size=len(jpeg_bytes),
                        total_frames=mjpeg_frames_total,
                    )
                except Exception as e:
                    log_ingest("mjpeg_frame_save_error", error=str(e))

            # Consume trailing CRLF after frame if present
            _ = f.readline()

    except Exception as e:
        log_ingest("mjpeg_client_handler_crashed", error=str(e), addr=str(addr))

    finally:
        mjpeg_clients -= 1
        try:
            conn.close()
        except Exception:
            pass
        log_ingest("mjpeg_client_disconnected", addr=str(addr), active_clients=mjpeg_clients)


# ---------------------------------------------------------
# PROTOCOL MULTIPLEXER
# ---------------------------------------------------------

def handle_client(conn, addr):
    """
    Multiplexer entrypoint.
    Peeks at the first bytes to decide whether this is:
      - JSON telemetry (line-delimited, starting with '{')
      - MJPEG stream (multipart, starting with '--frame' or JPEG headers)
    """
    try:
        first = conn.recv(8, socket.MSG_PEEK)
        if not first:
            log_ingest("ingest_empty_connection", addr=str(addr))
            conn.close()
            return

        if first.lstrip().startswith(b"{"):
            log_ingest("ingest_protocol_detected", protocol="json", first_bytes=first)
            handle_json_client(conn, addr)

        elif first.startswith(b"--frame") or first.startswith(b"\xff\xd8"):
            log_ingest("ingest_protocol_detected", protocol="mjpeg", first_bytes=first)
            handle_mjpeg_client(conn, addr)

        else:
            log_ingest("ingest_unknown_protocol_defaulting_json", first_bytes=first)
            handle_json_client(conn, addr)

    except Exception as e:
        log_ingest("ingest_client_handler_crashed", error=str(e), addr=str(addr))
        try:
            conn.close()
        except Exception:
            pass


# ---------------------------------------------------------
# TCP INGESTION SERVER
# ---------------------------------------------------------

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
