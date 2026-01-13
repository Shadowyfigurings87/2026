from arduino import start_arduino_threads, find_working_serial_port
from redrover_link.tcp_server import start_redrover_server
from ingest_unified import merged_stream
from ministries.network.uplink_ngrok import send_telemetry_and_receive_commands


def main():
    # Auto-detect Arduino serial port
    port = find_working_serial_port()

    if port is None:
        raise RuntimeError("No working serial port found for Arduino")

    # Start Arduino reader/writer
    start_arduino_threads(port=port, baud=115200)

    # Start RedRover link server
    start_redrover_server(host="0.0.0.0", port=9000)

    # Uplink to host via TCP (behind ngrok)
    send_telemetry_and_receive_commands(
        generator_factory=merged_stream,   # 🔥 FIXED
        host="4.tcp.ngrok.io",
        port=14846,
    )


if __name__ == "__main__":
    main()
