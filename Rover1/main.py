from arduino import start_arduino_threads
from redrover_link.tcp_server import start_redrover_server
from ingest_unified import merged_stream
from ministries.network.uplink_ngrok import send_telemetry_and_receive_commands

def main():
    # Start Arduino reader/writer
    start_arduino_threads(port="/dev/ttyACM0", baud=115200)

    # Start RedRover link server
    start_redrover_server(host="0.0.0.0", port=9100)

    # Unified telemetry stream
    stream = merged_stream()

    # Uplink to host via TCP (behind ngrok)
    # Change host/port to your ngrok-exposed endpoint
    send_telemetry_and_receive_commands(
        generator=stream,
        host="127.0.0.1",
        port=6000,
    )

if __name__ == "__main__":
    main()
