from arduino import start_arduino_threads, find_working_serial_port
from redrover_link.tcp_server import start_redrover_server
from ingest_unified import merged_stream
from ministries.network.uplink_ngrok import send_telemetry_and_receive_commands
from ministries.camera.streamer import MJPEGStreamer


def main():
    print("Rover1 main.py starting…")

    # Start MJPEG video streamer (video uplink)
    video = MJPEGStreamer(
        host="0.tcp.ngrok.io",
        port=12702,
        fps=10
    )
    video.start()

    # Auto-detect Arduino serial port
    port = find_working_serial_port()
    if port is None:
        raise RuntimeError("No working serial port found for Arduino")

    # Start Arduino reader/writer
    start_arduino_threads(port=port, baud=115200)

    # Start RedRover link server
    start_redrover_server(host="0.0.0.0", port=9000)

    # JSON telemetry uplink
    send_telemetry_and_receive_commands(
        generator_factory=merged_stream,
        host="0.tcp.ngrok.io",
        port=11092,
    )


if __name__ == "__main__":
    main()
