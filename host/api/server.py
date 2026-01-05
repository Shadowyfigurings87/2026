# host/api/server.py

import socket
import threading
import json
from datetime import datetime
from host.services.db_writer import write_queue, start_db_writer

HOST = "0.0.0.0"
PORT = 5000

def handle_client(conn, addr):
    print(f"[Host] Rover connected from {addr}")

    with conn, conn.makefile("r") as f:
        for line in f:
            try:
                obj = json.loads(line)
            except:
                continue

            ts = obj.get("ts")
            timestamp_utc = obj.get("timestamp")
            ministry = obj.get("ministry", "unknown")

            write_queue.put((
                "INSERT INTO telemetry_raw (timestamp_utc, ts, ministry, payload) VALUES (?, ?, ?, ?)",
                (timestamp_utc, ts, ministry, json.dumps(obj))
            ))

def start_server():
    start_db_writer()

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind((HOST, PORT))
    sock.listen(5)

    print(f"[Host] Listening on {HOST}:{PORT}")

    while True:
        conn, addr = sock.accept()
        threading.Thread(target=handle_client, args=(conn, addr), daemon=True).start()
