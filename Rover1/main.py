# Rover1/main.py

import threading
import time

from ministries.arduino.service import start_arduino_ministry
from ministries.camera.camera_ministry import start_camera_ministry
from ministries.network.uplink import send_unified_uplink
from ministries.ingestion.base  import merged_stream

# Telemetry tunnel (ngrok A)
TELEMETRY_HOST = "0.tcp.ngrok.io"
TELEMETRY_PORT = 16109


def main():
    print("\n==============================")
    print(" [Rover1] Boot Sequence Start ")
    print("==============================\n")

    # Arduino ministry
    print("[Rover1] Initializing Arduino ministry…")
    try:
        start_arduino_ministry()
        print("[Rover1] Arduino ministry started successfully")
    except Exception as e:
        print(f"[Rover1] ERROR: Arduino ministry failed to start: {e}")

    # Camera ministry (self-contained)
    print("\n[Rover1] Initializing Camera ministry (self-contained)…")
    try:
        start_camera_ministry()
        print("[Rover1] Camera ministry started successfully")
    except Exception as e:
        print(f"[Rover1] ERROR: Camera ministry failed to start: {e}")

    # Telemetry uplink
    print(f"\n[Rover1] Starting Telemetry uplink → {TELEMETRY_HOST}:{TELEMETRY_PORT}")
    print("[Rover1] Telemetry generator initializing…")
    try:
        tg = merged_stream()
        print("[Rover1] Telemetry generator ready")
    except Exception as e:
        print(f"[Rover1] ERROR: Failed to create telemetry generator: {e}")
        tg = None

    print("[Rover1] Entering unified telemetry uplink loop…")
    try:
        send_unified_uplink(
            host=TELEMETRY_HOST,
            port=TELEMETRY_PORT,
            telemetry_generator=tg,
        )
    except Exception as e:
        print(f"[Rover1] ERROR: Telemetry uplink crashed: {e}")

    print("\n[Rover1] MAIN LOOP EXITED — this should never happen\n")


if __name__ == "__main__":
    print("[Rover1] Executing main()…")
    main()
