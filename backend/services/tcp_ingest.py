import socket
import threading
import json
import time
from queue import Queue

from backend.services.shared_queue import ingest_queue  
from backend.utils.logging_config import log_event


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
                    raw_line, buffer = buffer.split(b"\n", 1)
                    line = raw_line.decode("utf-8", errors="ignore").strip()

                    if not line:
                        continue

                    try:
                        packet = json.loads(line)

                        # --- NEW: classify packet type ---
                        kind = packet.get("kind")

                        if kind == "telemetry":
                            # Rover telemetry
                            log_event(
                                component="tcp_ingest",
                                severity="DEBUG",
                                event="telemetry_received",
                                details={
                                    "rover": packet.get("rover", "unknown"),
                                    "source": packet.get("source", "unknown")
                                }
                            )

                        elif kind == "command_ack":
                            # Rover command acknowledgement
                            log_event(
                                component="tcp_ingest",
                                severity="DEBUG",
                                event="command_ack_received",
                                details=packet
                            )

                        else:
                            # RF frame or unknown packet
                            log_event(
                                component="tcp_ingest",
                                severity="DEBUG",
                                event="frame_received",
                                details={"kind": kind}
                            )

                        # Push into unified ingest queue
                        ingest_queue.put(packet)
                        frames_received += 1

                    except json.JSONDecodeError:
                        log_event(
                            component="tcp_ingest",
                            severity="WARNING",
                            event="json_decode_error",
                            details={"line": line[:200]}
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
    server.listen(5)

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
