# host/services/connect/json_handler.py

import json
import base64

from host.logs.wrappers import log_ingest
from host.services.metrics import (
    ingest_total,
    ingestion_queue_depth,
    update_rover_heartbeat,
)

from .worker import ingestion_queue, process_arduino_frame
from .command_bus import set_rover_socket
from host.services.connect.esp32_handler import handle_esp32_json
from host.services.db_writer import write_queue


# ============================================================
# SANITIZER — ensure DB-safe JSON
# ============================================================

def sanitize_for_json(obj: dict) -> dict:
    """
    Ensure the payload is JSON-serializable before DB enqueue.
    Converts bytes, sets, or other non-serializable types into safe strings.
    """
    safe = {}

    for k, v in obj.items():
        if isinstance(v, (bytes, bytearray)):
            safe[k] = base64.b64encode(v).decode()
        elif isinstance(v, set):
            safe[k] = list(v)
        elif isinstance(v, dict):
            safe[k] = sanitize_for_json(v)
        else:
            safe[k] = v

    return safe


# ============================================================
# MINISTRY ROUTER
# ============================================================

def route_ministry(obj, ministry):
    """
    Dispatch JSON payloads to the correct ministry handler.
    This is where ministries perform immediate side-effects
    (decoding, metrics, state updates).
    """
    # ESP32 → metrics + state
    if ministry == "esp32":
        handle_esp32_json(obj)
        return

    # Arduino → decode + upsert
    if ministry == "arduino":
        process_arduino_frame(obj)
        return

    # RF → handled by worker (RF frames are raw)
    if ministry == "rf":
        log_ingest("rf_frame_received_stub", payload=obj)
        return

    # System events
    if ministry == "system":
        log_ingest("system_event", payload=obj)
        return

    # Unknown
    log_ingest("ingest_unknown_ministry", payload=obj)


# ============================================================
# MAIN INGESTION LOOP
# ============================================================

def handle_json_client(conn, addr):
    """
    Handles line-delimited JSON telemetry from any ministry.
    Camera frames are no longer processed here.
    """
    log_ingest("json_client_connected", addr=str(addr))
    set_rover_socket(conn)

    try:
        with conn, conn.makefile("r") as f:
            for line in f:
                log_ingest("json_line_received", raw=line)

                # Parse JSON safely
                try:
                    obj = json.loads(line)
                except Exception as e:
                    log_ingest("json_decode_error", error=str(e), raw=line)
                    continue

                # Heartbeat
                update_rover_heartbeat()

                # Determine ministry
                ministry = (
                    obj.get("ministry")
                    or obj.get("device")
                    or "unknown"
                )

                # Ministry-specific processing
                route_ministry(obj, ministry)

                # Queue for ingestion worker
                ingest_total.inc()
                ingestion_queue.put(obj)
                ingestion_queue_depth.set(ingestion_queue.qsize())

                # Prepare DB-safe payload
                safe_obj = sanitize_for_json(obj)

                # Queue DB write
                try:
                    ts = obj.get("ts")
                    timestamp_utc = obj.get("timestamp")
                    write_queue.put((
                        "INSERT INTO telemetry_raw (timestamp_utc, ts, ministry, payload) "
                        "VALUES (?, ?, ?, ?)",
                        (timestamp_utc, ts, ministry, json.dumps(safe_obj)),
                    ))
                except Exception as e:
                    log_ingest("db_enqueue_error", error=str(e), payload=obj)

    except Exception as e:
        log_ingest("json_client_crashed", error=str(e), addr=str(addr))
