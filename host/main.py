# host/main.py

import threading
import time

from host.services.connect.server import start_ingestion_server
from host.services.camera.server import start_camera_server
from host.api_server import start_api_server
from host.logs.wrappers import log_ingest
from host.services.db_writer import start_db_writer
from host.services.command_pipeline.command_server import command_server


def start_host():
    print("\n==============================")
    print("   HOST BACKEND STARTING…")
    print("==============================\n")

    log_ingest("host_starting")

    # -------------------------------------------------------
    # DB WRITER MINISTRY
    # -------------------------------------------------------
    print("[Host] Starting DB writer ministry…")
    start_db_writer()

    # -------------------------------------------------------
    # INGESTION MINISTRY (port 5000)
    # -------------------------------------------------------
    print("[Host] Starting ingestion ministry on port 5000…")
    threading.Thread(
        target=start_ingestion_server,
        daemon=True
    ).start()

    # -------------------------------------------------------
    # CAMERA MINISTRY (port 5001)
    # -------------------------------------------------------
    print("[Host] Starting camera ministry on port 5001…")
    threading.Thread(
        target=start_camera_server,
        daemon=True
    ).start()

    # -------------------------------------------------------
    # API MINISTRY (port 8000)
    # -------------------------------------------------------
    print("[Host] Starting API ministry on port 8000…")
    threading.Thread(
        target=start_api_server,
        daemon=True
    ).start()

    print("[Host] All ministries launched. Entering heartbeat loop.\n")
    log_ingest("host_ministries_started")

    # -------------------------------------------------------
    # HEARTBEAT LOOP
    # -------------------------------------------------------
    while True:
        time.sleep(5)
        log_ingest("host_alive")


if __name__ == "__main__":
    start_host()
