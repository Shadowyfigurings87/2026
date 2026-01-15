# host/services/ingest.py

from host.logs.wrappers import log_ingest, log_rf
from host.services.frame_store import save_frame

import socket
import threading
import json
import time
import base64
import asyncio
from queue import Queue

from host.services.db_writer import write_queue
from host.services.metrics import (
    ingest_total,
    ingestion_queue_depth,
    rf_frames_total,
    rf_frame_processing_seconds,
)

from host.api.router import app as fastapi_app

HOST = "0.0.0.0"
PORT = 5000

ingestion_queue = Queue()

latest_frame_bytes = None
latest_frame_timestamp = None

MJPEG_SAVE_EVERY_N = 5

mjpeg_clients = 0
mjpeg_frames_total = 0
mjpeg_bytes_total = 0


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


def handle_json_client(conn, addr):
    log_ingest("ingest_json_client_connected", addr=str(addr))
    try:
        with conn, conn.makefile("r") as f:
            for line in f:
                log_ingest("ingest_raw_line_received", raw=line)
                try:
                    obj = json.loads(line)
                except Exception as e:
                    log_ingest("ingest_json_decode_error", error=str(e), raw=line)
                    continue
                ministry = (
                    obj.get("ministry")
                    or obj.get("device")
                    or ("picamera2" if "frame" in obj else "unknown")
                )
                if "frame" in obj:
                    frame_b64 = obj.pop("frame", None)
                    if frame_b64:
                        try:
                            binary = base64.b64decode(frame_b64)
                            path = save_frame(binary)
                            obj["frame_path"] = path
                        except Exception as e:
                            log_ingest("camera_frame_decode_error", error=str(e))
                ingest_total.inc()
                ingestion_queue.put(obj)
                ingestion_queue_depth.set(ingestion_queue.qsize())
                try:
                    ts = obj.get("ts")
                    timestamp_utc = obj.get("timestamp")
                    write_queue.put(
                        (
                            "INSERT INTO telemetry_raw (timestamp_utc, ts, ministry, payload) VALUES (?, ?, ?, ?)",
                            (timestamp_utc, ts, ministry, json.dumps(obj)),
                        )
                    )
                except Exception as e:
                    log_ingest("ingest_db_enqueue_error", error=str(e), payload=obj)
    except Exception as e:
        log_ingest("ingest_json_client_handler_crashed", error=str(e), addr=str(addr))


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
            boundary = f.readline()
            if not boundary:
                break
            if not boundary.startswith(b"--frame"):
                log_ingest("mjpeg_unexpected_boundary", boundary=boundary[:64])
                continue
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
            jpeg_bytes = f.read(length)
            if not jpeg_bytes or len(jpeg_bytes) < length:
                log_ingest(
                    "mjpeg_incomplete_frame",
                    expected=length,
                    got=len(jpeg_bytes or b""),
                )
                break
            mjpeg_frames_total += 1
            mjpeg_bytes_total += len(jpeg_bytes)
            frame_counter += 1
            _update_latest_frame(jpeg_bytes)
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
            _ = f.readline()
    except Exception as e:
        log_ingest("mjpeg_client_handler_crashed", error=str(e), addr=str(addr))
    finally:
        mjpeg_clients -= 1
        try:
            conn.close()
        except Exception:
            pass
        log_ingest(
            "mjpeg_client_disconnected", addr=str(addr), active_clients=mjpeg_clients
        )


def _parse_http_request(f):
    request_line = f.readline()
    if not request_line:
        return None, None, None, {}, b""
    try:
        request_line_str = request_line.decode("iso-8859-1").strip()
        method, target, version = request_line_str.split(" ", 2)
    except ValueError:
        return None, None, None, {}, b""
    headers = {}
    while True:
        line = f.readline()
        if not line or line in (b"\r\n", b"\n"):
            break
        try:
            line_str = line.decode("iso-8859-1")
            key, value = line_str.split(":", 1)
            headers[key.strip().lower()] = value.strip()
        except ValueError:
            continue
    body = b""
    content_length = headers.get("content-length")
    if content_length is not None:
        try:
            length = int(content_length)
            if length > 0:
                body = f.read(length)
        except ValueError:
            pass
    return method, target, version, headers, body


async def _asgi_call(app, scope, body_bytes):
    response = {"status": 500, "headers": [], "body": b""}

    async def receive():
        nonlocal body_bytes
        if body_bytes is None:
            return {"type": "http.request", "body": b"", "more_body": False}
        b = body_bytes
        body_bytes = None
        return {"type": "http.request", "body": b, "more_body": False}

    async def send(message):
        if message["type"] == "http.response.start":
            response["status"] = message.get("status", 200)
            response["headers"] = message.get("headers", [])
        elif message["type"] == "http.response.body":
            body_part = message.get("body", b"")
            if body_part:
                response["body"] += body_part

    await app(scope, receive, send)
    return response


def handle_http_client(conn, addr):
    log_ingest("http_client_connected", addr=str(addr))
    try:
        f = conn.makefile("rb")
        method, target, version, headers, body = _parse_http_request(f)
        if method is None:
            log_ingest("http_parse_error", addr=str(addr))
            return
        if "?" in target:
            path, qs = target.split("?", 1)
        else:
            path, qs = target, ""
        scope = {
            "type": "http",
            "http_version": "1.1",
            "method": method,
            "scheme": "http",
            "path": path,
            "raw_path": path.encode("utf-8"),
            "query_string": qs.encode("utf-8"),
            "headers": [
                (k.encode("latin-1"), v.encode("latin-1"))
                for k, v in headers.items()
            ],
            "client": addr,
            "server": (HOST, PORT),
        }
        response = asyncio.run(_asgi_call(fastapi_app, scope, body))
        status = response["status"]
        body_bytes = response["body"]
        resp_headers = response["headers"]
        reason = "OK" if 200 <= status < 300 else "ERROR"
        conn.sendall(f"HTTP/1.1 {status} {reason}\r\n".encode("iso-8859-1"))
        has_content_length = any(
            k.lower() == b"content-length" for k, _ in resp_headers
        )
        if not has_content_length:
            resp_headers.append(
                (b"content-length", str(len(body_bytes)).encode("latin-1"))
            )
        has_connection = any(k.lower() == b"connection" for k, _ in resp_headers)
        if not has_connection:
            resp_headers.append((b"connection", b"close"))
        for k, v in resp_headers:
            conn.sendall(k + b": " + v + b"\r\n")
        conn.sendall(b"\r\n")
        if body_bytes:
            conn.sendall(body_bytes)
        log_ingest("http_client_served", addr=str(addr), status=status, path=path)
    except Exception as e:
        log_ingest("http_client_handler_crashed", error=str(e), addr=str(addr))
    finally:
        try:
            conn.close()
        except Exception:
            pass
        log_ingest("http_client_disconnected", addr=str(addr))


def handle_client(conn, addr):
    try:
        first = conn.recv(64, socket.MSG_PEEK)
        if not first:
            log_ingest("ingest_empty_connection", addr=str(addr))
            conn.close()
            return

        stripped = first.lstrip()

        # 1. HTTP FIRST
        if (
            stripped.startswith(b"GET")
            or stripped.startswith(b"POST")
            or stripped.startswith(b"HEAD")
            or stripped.startswith(b"PUT")
            or stripped.startswith(b"DELETE")
            or stripped.startswith(b"OPTIONS")
        ):
            print("🔥 HTTP DETECTED 🔥")
            handle_http_client(conn, addr)
            return

        # 2. JSON SECOND
        if stripped.startswith(b"{"):
            print("🔥 JSON DETECTED 🔥")
            handle_json_client(conn, addr)
            return

        # 3. MJPEG THIRD
        if first.startswith(b"--frame") or first.startswith(b"\xff\xd8"):
            print("🔥 MJPEG DETECTED 🔥")
            handle_mjpeg_client(conn, addr)
            return

        # 4. FALLBACK
        print("🔥 FALLBACK TO JSON 🔥")
        handle_json_client(conn, addr)

    except Exception as e:
        log_ingest("ingest_client_handler_crashed", error=str(e), addr=str(addr))
        try:
            conn.close()
        except:
            pass

def start_ingestion_server():
    log_ingest("ingestion_server_start")
    threading.Thread(target=worker_loop, daemon=True).start()
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind((HOST, PORT))
    sock.listen(5)
    log_ingest("ingestion_server_listening", host=HOST, port=PORT)
    while True:
        conn, addr = sock.accept()
        threading.Thread(target=handle_client, args=(conn, addr), daemon=True).start()
