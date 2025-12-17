# ingest/ingest_tcp_server.py

import socket
import threading
import json
from queue import Queue

# The manager will pass this in
INGEST_QUEUE: Queue = None

HOST = "0.0.0.0"
PORT = 9000
BACKLOG = 5
BUF_SIZE = 4096


def handle_client(conn, addr):
    """
    Handle a single TCP client connection.
    Reads JSON lines and pushes them into the ingest queue.
    """
    print(f"[TCP] Sensor connected: {addr}")

    buffer = ""

    try:
        while True:
            data = conn.recv(BUF_SIZE)
            if not data:
                break

            buffer += data.decode("utf-8", errors="ignore")

            # Process complete lines
            while "\n" in buffer:
                line, buffer = buffer.split("\n", 1)
                line = line.strip()
                if not line:
                    continue

                try:
                    frame = json.loads(line)
                    INGEST_QUEUE.put(frame)
                except Exception as e:
                    print(f"[TCP] JSON parse error: {e}")

    except Exception as e:
        print(f"[TCP] Client error: {e}")

    finally:
        conn.close()
        print(f"[TCP] Sensor disconnected: {addr}")


def start_tcp_ingest_server(queue: Queue):
    """
    Start the TCP ingest server in a background thread.
    """
    global INGEST_QUEUE
    INGEST_QUEUE = queue

    def server_thread():
        print(f"[TCP] Ingest server listening on {HOST}:{PORT}")
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((HOST, PORT))
        s.listen(BACKLOG)

        while True:
            conn, addr = s.accept()
            t = threading.Thread(target=handle_client, args=(conn, addr), daemon=True)
            t.start()

    t = threading.Thread(target=server_thread, daemon=True)
    t.start()
 