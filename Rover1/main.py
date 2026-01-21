# /home/balthazaar87/2026/Rover1/main.py

import os
import sys

print("DEBUG: CWD =", os.getcwd())
print("DEBUG: sys.path =", sys.path)

# Correct imports for a script executed inside the Rover1 directory
from arduino import start_arduino_threads
from redrover_link.tcp_server import start_redrover_server
from ministries.network.uplink import send_unified_uplink


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
    # Unified uplink (telemetry + camera + commands)
    # ---------------------------------------------------------
    HOST = "2.tcp.ngrok.io"
    PORT = 13023

    print(f"Starting unified uplink to {HOST}:{PORT}…")
    send_unified_uplink(
        host=HOST,
        port=PORT,
        reconnect_delay=5,
        heartbeat_interval=5,
        camera_fps=10,
        camera_weight=5,
    )


if __name__ == "__main__":
    main()
