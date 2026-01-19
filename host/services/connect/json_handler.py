# host/services/connect/json_handler.py

import json
import base64

from host.logs.wrappers import log_ingest
from host.services.frame_store import save_frame, store_latest_frame
from host.services.db_writer import write_queue
from host.services.metrics import (
    ingest_total,
    ingestion_queue_depth,
    update_rover_heartbeat,   # already imported
)

from .worker import ingestion_queue
from .command_bus import set_rover_socket
from host.services.metrics import update_camera_frame

# Ministry handlers
from host.services.connect.esp32_handler import handle_esp32_json


def handle_json_client(conn, addr):
    log_ingest("json_client_connected", addr=str(addr))
    set_rover_socket(conn)

    try:
        with conn, conn.makefile("r") as f:
            for line in f:
                log_ingest("json_line_received", raw=line)

                try:
                    obj = json.loads(line)
                except Exception as e:
                    log_ingest("json_decode_error", error=str(e), raw=line)
                    continue

                # ✅ every valid rover packet updates heartbeat
                update_rover_heartbeat()

                ministry = (
                    obj.get("ministry")
                    or obj.get("device")
                    or ("picamera2" if "frame" in obj else "unknown")
                )

                frame_b64 = (
                    obj.pop("frame", None)
                    or obj.pop("jpeg", None)
                    or obj.pop("data", None)
                )

                if frame_b64:
                    try:
                        binary = base64.b64decode(frame_b64)
                        update_camera_frame()
                        store_latest_frame(binary)
                        path = save_frame(binary)
                        obj["frame_path"] = path
                        log_ingest("camera_frame_ingested", size=len(binary))
                    except Exception as e:
                        log_ingest("camera_frame_decode_error", error=str(e))

                # ✅ route to ministry handler (ESP32, etc.)
                route_ministry(obj, ministry)

                # queue for ingestion worker
                ingest_total.inc()
                ingestion_queue.put(obj)
                ingestion_queue_depth.set(ingestion_queue.qsize())

                safe_obj = sanitize_for_json(obj)

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
