# Rover1/main.py

import threading
from ministries.arduino.service import start_arduino_ministry
from ministries.camera.camera_ministry import start_camera_ministry
from ministries.network.uplink import send_unified_uplink
from ministries.ingestion.ingest import telemetry_generator

HOST = "2.tcp.ngrok.io"      # your telemetry ngrok domain
PORT = 12690                 # your telemetry ngrok port

def main():
    print("[Rover1] Starting ministries...")

    # Arduino ministry
    start_arduino_ministry()

    # Camera ministry
    start_camera_ministry()

    # Telemetry uplink (runs forever)
    send_unified_uplink(
        host=HOST,
        port=PORT,
        telemetry_generator=telemetry_generator(),
    )

if __name__ == "__main__":
    main()
