# host/api/server.py

import socket
import threading
import json
import time
from queue import Queue

from host.services.db_writer import write_queue, start_db_writer
from host.services.metrics import (
    ingest_total,
    ingestion_queue_depth,
    rf_frames_total,
    rf_frame_processing_seconds,
)

HOST = "0.0.0.0"
PORT = 5000

# ---------------------------------------------------------
# GLOBAL INGESTION QUEUE
# ---------------------------------------------------------
ingestion_queue = Queue()


# ---------------------------------------------------------
# PROCESSING FUNCTIONS
# ---------------------------------------------------------

def process_rf_frame(msg: dict):
    """
    Process an RF frame and record metrics.
    """
    start = time.perf_counter()
    try:
        rf_frames_total.inc()
        # TODO: add your RF processing logic here
    finally:
        duration = time.perf_counter() - start
        rf_frame_processing_seconds.observe(duration)


def worker_loop():
    """
    Worker thread that consumes messages from the ingestion queue.
    """
    while True:
        msg = ingestion_queue.get()
        try:
            # Dispatch based on message type
            if msg.get("device") == "picamera2":
                process_rf_frame(msg)
            # Add other ministries here...
        finally:
            ingestion_queue_depth.set(ingestion_queue.qsize())
            ingestion_queue.task_done()


# ---------------------------------------------------------
# TCP INGESTION SERVER
# ---------------------------------------------------------

def handle_client(conn, addr):
    print(f"[Host] Rover connected from {addr}")

    try:
        with conn, conn.makefile("r") as f:
            for line in f:
                print("[Host] RAW LINE:", repr(line))

                try:
                    obj = json.loads(line)
                except Exception as e:
                    print("[Host] JSON decode error:", e)
                    continue

                # -----------------------------
                # PROMETHEUS METRICS UPDATE
                # -----------------------------
                ingest_total.inc()
                ingestion_queue.put(obj)
                ingestion_queue_depth.set(ingestion_queue.qsize())
                # -----------------------------

                # Push raw JSON into DB writer queue
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
    print("[Host] Starting ingestion server...")

    # Start DB writer thread
    start_db_writer()

    # Start ingestion worker thread
    threading.Thread(target=worker_loop, daemon=True).start()

    # Start TCP server
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind((HOST, PORT))
    sock.listen(5)

    print(f"[Host] Listening on {HOST}:{PORT}")

    while True:
        conn, addr = sock.accept()
        threading.Thread(target=handle_client, args=(conn, addr), daemon=True).start()
