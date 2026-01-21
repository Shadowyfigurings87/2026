# /home/balthazaar87/2026/Rover1/main.py

import os
import sys

print("DEBUG: CWD =", os.getcwd())
print("DEBUG: sys.path =", sys.path)

# ---------------------------------------------------------
# Ministry imports
# ---------------------------------------------------------
from arduino import start_arduino_threads
from redrover_link.tcp_server import start_redrover_server

# NEW: unified ingestion ministry (modularized)
from ministries.ingestion.base import merged_stream

# Unified uplink (telemetry + commands)
from ministries.network.uplink import send_unified_uplink

# NEW: camera ministry (independent MJPEG uplink)
from ministries.camera import start_camera_ministry


def main():
    print("Rover1 main.py starting…")

    # ---------------------------------------------------------
    # Start Arduino ministry (auto-discovery + reconnect logic)
    # ---------------------------------------------------------
    print("Starting Arduino ministry…")
    start_arduino_threads()

    # ---------------------------------------------------------
    # Start RedRover link server (local TCP server for rover control)
    # ---------------------------------------------------------
    print("Starting RedRover TCP server on port 9000…")
    start_redrover_server(host="0.0.0.0", port=9000)

    # ---------------------------------------------------------
    # Start Camera ministry (independent MJPEG uplink)
    # ---------------------------------------------------------
    print("Starting Camera ministry…")
    start_camera_ministry()

    # ---------------------------------------------------------
    # Unified uplink (telemetry + commands)
    # Now powered by the new ingestion ministry
    # ---------------------------------------------------------
    HOST = "2.tcp.ngrok.io"
    PORT = 13023

    print(f"Starting unified uplink to {HOST}:{PORT}…")

    uplink_gen = merged_stream()

    send_unified_uplink(
        host=HOST,
        port=PORT,
        reconnect_delay=5,
        heartbeat_interval=5,
        telemetry_generator=uplink_gen,
    )


if __name__ == "__main__":
    main()
