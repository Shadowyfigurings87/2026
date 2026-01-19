# host/services/connect/json_handler.py

import json
import base64

from host.logs.wrappers import log_ingest
from host.services.frame_store import save_frame, store_latest_frame
from host.services.db_writer import write_queue
from host.services.metrics import ingest_total, ingestion_queue_depth

from .worker import ingestion_queue
from .command_bus import set_rover_socket

# Ministry handlers
from host.services.connect.esp32_handler import handle_esp32_json
# from host.services.connect.arduino_handler import handle_arduino_json
# from host.services.connect.rf_handler import handle_rf_json


def sanitize_for_json(obj: dict) -> dict:
    """
    Ensure the payload is JSON-serializable before DB enqueue.
    Converts bytes, sets, or other non-serializable types into safe strings.
    """
    safe = {}

    for k, v in obj.items():
        # Bytes → base64 string
        if isinstance(v, (bytes, bytearray)):
            safe[k] = base64.b64encode(v).decode()

        # Sets → lists
        elif isinstance(v, set):
            safe[k] = list(v)

        # Nested dicts → sanitize recursively
        elif isinstance(v, dict):
            safe[k] = sanitize_for_json(v)

        # Everything else → let json.dumps handle it
        else:
            safe[k] = v

    return safe


def route_ministry(obj, ministry):
    """
    Dispatch JSON payloads to the correct ministry handler.
    """
    if ministry == "esp32":
        handle_esp32_json(obj)
        return

    if ministry == "arduino":
        log_ingest("arduino_frame_stub", payload=obj)
        return

    if ministry == "rf":
        log_ingest("rf_frame_stub", payload=obj)
        return

    if ministry == "picamera2":
        return

    if ministry == "system":
        log_ingest("system_event", payload=obj)
        return

    log_ingest("ingest_unknown_ministry", payload=obj)


def handle_json_client(conn, addr):
    """
    Handles line-delimited JSON telemetry and optionally registers this socket
    as the rover control/telemetry uplink.
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

                # Determine ministry
                ministry = (
                    obj.get("ministry")
                    or obj.get("device")
                    or ("picamera2" if "frame" in obj else "unknown")
                )

                # Camera frame handling
                if "frame" in obj:
                    frame_b64 = obj.pop("frame", None)
                    if frame_b64:
                        try:
                            binary = base64.b64decode(frame_b64)
                            store_latest_frame(binary)
                            path = save_frame(binary)
                            obj["frame_path"] = path
                        except Exception as e:
                            log_ingest("camera_frame_decode_error", error=str(e))

                # Route to ministry handler
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
