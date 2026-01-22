# Rover1/main.py

import threading

from ministries.arduino.service import start_arduino_ministry
from ministries.camera.camera_ministry import start_camera_ministry
from ministries.network.uplink import send_unified_uplink
from ministries.ingestion.ingest import telemetry_generator

# Telemetry tunnel (ngrok A)
TELEMETRY_HOST = "8.tcp.ngrok.io"
TELEMETRY_PORT = 19760

# Camera tunnel (ngrok B)
# These values come from ministries/camera/config.py
# but you can override them here if needed.
from ministries.camera.config import HOST as CAMERA_HOST, PORT as CAMERA_PORT


def main():
    print("[Rover1] Starting ministries...")

    # Arduino ministry (local)
    start_arduino_ministry()

    # Camera ministry (local capture + encoding + its own uplink)
    start_camera_ministry()

    # Telemetry uplink (separate TCP client)
    send_unified_uplink(
        host=TELEMETRY_HOST,
        port=TELEMETRY_PORT,
        telemetry_generator=telemetry_generator(),
    )


if __name__ == "__main__":
    main()
