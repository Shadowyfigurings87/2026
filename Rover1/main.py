# Rover1/main.py

import threading
import time

from Rover1.ministries.network.redrover_server import start_redrover_server
from Rover1.ministries.arduino.service import start_arduino_ministry
from Rover1.ministries.arduino import state
from Rover1.ministries.camera.camera_ministry import start_camera_ministry
from Rover1.ministries.ingestion.base import merged_stream
from Rover1.ministries.network.uplink import send_unified_uplink

# Telemetry tunnel (ngrok A)
TELEMETRY_HOST = "0.tcp.ngrok.io"
TELEMETRY_PORT = 16109


def main():
    print("\n==============================")
    print(" [Rover1] Boot Sequence Start ")
    print("==============================\n")

    # ---------------------------------------------------------
    # 1. Arduino Ministry
    # ---------------------------------------------------------
    print("[Rover1] Starting Arduino ministry…")
    threading.Thread(
        target=start_arduino_ministry,
        daemon=True,
        name="ArduinoMinistry",
    ).start()

    # ---------------------------------------------------------
    # WAIT FOR ARDUINO MINISTRY TO INITIALIZE
    # ---------------------------------------------------------
    print("[Rover1] Waiting for Arduino ministry to become ready…")
    while not state.arduino_ready:
        time.sleep(0.1)
    print("[Rover1] Arduino ministry is ready")

    # ---------------------------------------------------------
    # 2. Camera Ministry
    # ---------------------------------------------------------
    print("[Rover1] Starting Camera ministry…")
    threading.Thread(
        target=start_camera_ministry,
        daemon=True,
        name="CameraMinistry",
    ).start()

    print("[Rover1] Starting RedRoverLink server…")
    threading.Thread(
        target=start_redrover_server,
        daemon=True,
        name="RedRoverLink",
    ).start()
	
    # ---------------------------------------------------------
    # 3. Ingestion Ministry (merged_stream generator)
    # ---------------------------------------------------------
    print("[Rover1] Initializing ingestion (merged_stream)…")
    try:
        telemetry_gen = merged_stream()
        print("[Rover1] Ingestion ministry ready")
    except Exception as e:
        print(f"[Rover1] ERROR: Failed to initialize ingestion: {e}")
        telemetry_gen = None

    # ---------------------------------------------------------
    # 4. Uplink Ministry
    # ---------------------------------------------------------
    print(f"[Rover1] Starting uplink → {TELEMETRY_HOST}:{TELEMETRY_PORT}")
    threading.Thread(
        target=send_unified_uplink,
        args=(TELEMETRY_HOST, TELEMETRY_PORT, telemetry_gen),
        daemon=True,
        name="UplinkMinistry",
    ).start()

    print("\n[Rover1] All ministries launched. Entering heartbeat loop.\n")

    # ---------------------------------------------------------
    # 5. Main heartbeat loop (never exits)
    # ---------------------------------------------------------
    while True:
        print("[Rover1] heartbeat")
        time.sleep(5)


if __name__ == "__main__":
    print("[Rover1] Executing main()…")
    main()
