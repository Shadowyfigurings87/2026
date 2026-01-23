# Rover1/ministries/network/redrover_server.py

import socket
import threading
import traceback

from Rover1.ministries.ingestion.streams.redrover_stream import push_redrover_line


HOST = "0.0.0.0"
PORT = 9000


def _handle_client(conn, addr):
    """
    Handles a single RedRover client connection.
    Reads JSONL lines and forwards them into ingestion.
    """
    print(f"[RedRoverLink] Client connected: {addr}")

    try:
        with conn:
            buf = b""

            while True:
                chunk = conn.recv(4096)
                if not chunk:
                    print(f"[RedRoverLink] Client disconnected: {addr}")
                    return

                buf += chunk

                # Process all complete lines
                while b"\n" in buf:
                    raw_line, buf = buf.split(b"\n", 1)

                    try:
                        line = raw_line.decode("utf-8", errors="ignore").strip()
                    except Exception:
                        print(f"[RedRoverLink] UTF-8 decode error from {addr}")
                        continue

                    if not line:
                        continue

                    print(f"[RedRoverLink] {addr} → {line}")

                    # Push into ingestion
                    push_redrover_line(line)

    except Exception as e:
        print(f"[RedRoverLink] ERROR in client handler {addr}: {e}")
        print(traceback.format_exc())

    finally:
        print(f"[RedRoverLink] Connection closed: {addr}")


def start_redrover_server(host=HOST, port=PORT):
    """
    Starts the RedRoverLink TCP server.
    Accepts multiple reconnects and multiple clients.
    """
    print(f"[RedRoverLink] Starting server on {host}:{port}")

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((host, port))
    s.listen(5)

    print("[RedRoverLink] Server listening")

    def accept_loop():
        while True:
            try:
                conn, addr = s.accept()
                print(f"[RedRoverLink] Connection from {addr}")

                t = threading.Thread(
                    target=_handle_client,
                    args=(conn, addr),
                    daemon=True,
                    name=f"RedRoverClient-{addr[0]}:{addr[1]}"
                )
                t.start()

            except Exception as e:
                print(f"[RedRoverLink] ERROR in accept loop: {e}")
                print(traceback.format_exc())

    threading.Thread(target=accept_loop, daemon=True, name="RedRoverAcceptLoop").start()
