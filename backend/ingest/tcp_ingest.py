import socket
import threading
import json
import time
from queue import Queue

# Adjust this import to match your actual queue location
from ingest.shared_queue import ingest_queue  

from utils.logging import log_event  # Your structured logging helper


def handle_client(conn, addr):
    log_event(
        component="tcp_ingest",
        severity="INFO",
        event="client_connected",
        details={"addr": addr}
    )

    buffer = b""
    frames_received = 0
    start_time = time.time()

    try:
        with conn:
            while True:
                data = conn.recv(4096)
                if not data:
                    break

                buffer += data

                # Process JSON lines
                while b"\n" in buffer:
                    line, buffer = buffer.split(b"\n", 1)
                    try:
                        frame = json.loads(line.decode("utf-8").strip())
                        ingest_queue.put(frame)
                        frames_received += 1
                    except Exception as e:
                        log_event(
                            component="tcp_ingest",
                            severity="WARNING",
                            event="json_decode_error",
                            details={"line": line[:200].decode("utf-8", errors="ignore")}
                        )
                        continue

    except Exception as e:
        log_event(
            component="tcp_ingest",
            severity="ERROR",
            event="client_error",
            details={"addr": addr, "error": str(e)}
        )

    finally:
        elapsed = time.time() - start_time
        log_event(
            component="tcp_ingest",
            severity="INFO",
            event="client_disconnected",
            details={
                "addr": addr,
                "frames_received": frames_received,
                "uptime_sec": round(elapsed, 2)
            }
        )


def start_tcp_ingest(host="0.0.0.0", port=9000):
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((host, port))
    server.listen(1)

    log_event(
        component="tcp_ingest",
        severity="INFO",
        event="tcp_ingest_online",
        details={"host": host, "port": port}
    )

    def accept_loop():
        while True:
            conn, addr = server.accept()
            threading.Thread(
                target=handle_client,
                args=(conn, addr),
                daemon=True
            ).start()

    threading.Thread(target=accept_loop, daemon=True).start()
