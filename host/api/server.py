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

    try:
        with conn, conn.makefile("r") as f:
            for line in f:
                print("[Host] RAW LINE:", repr(line))   # <--- ADD THIS
                try:
                    obj = json.loads(line)
                except Exception as e:
                    print("[Host] JSON decode error:", e)
                    continue

                try:
                    ts = obj.get("ts")
                    timestamp_utc = obj.get("timestamp")
                    ministry = obj.get("ministry", "unknown")

                    write_queue.put((
                        "INSERT INTO telemetry_raw (timestamp_utc, ts, ministry, payload) VALUES (?, ?, ?, ?)",
                        (timestamp_utc, ts, ministry, json.dumps(obj))
                    ))
                except Exception as e:
                    print("[Host] Processing error:", e)
    except Exception as e:
        print("[Host] Client handler crashed:", e)

def start_server():
    start_db_writer()

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind((HOST, PORT))
    sock.listen(5)

    print(f"[Host] Listening on {HOST}:{PORT}")

    while True:
        conn, addr = sock.accept()
        threading.Thread(target=handle_client, args=(conn, addr), daemon=True).start()
