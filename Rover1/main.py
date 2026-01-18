# /home/zachariah/2026/Rover1/main.py

from arduino import start_arduino_threads, find_working_serial_port
from redrover_link.tcp_server import start_redrover_server
from ministries.network.uplink import send_unified_uplink


def main():
    print("Rover1 main.py starting…")

    # Auto-detect Arduino serial port
    port = find_working_serial_port()
    if port is None:
        raise RuntimeError("No working serial port found for Arduino")

    print(f"Arduino detected on {port}, starting threads…")
    start_arduino_threads(port=port, baud=115200)

    # Start RedRover link server (local TCP server for rover control)
    print("Starting RedRover TCP server on port 9000…")
    start_redrover_server(host="0.0.0.0", port=9000)

    # Unified uplink (telemetry + camera + commands)
    # Connect to ngrok TCP tunnel
    HOST = "0.tcp.ngrok.io"   # <-- correct ngrok hostname
    PORT = 11092              # <-- your ngrok TCP port

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
