# Rover1/ministries/camera/mjpeg_client.py
#
# RAW JPEG uplink client (replaces old HTTP MJPEG POST)
# - Keeps the same function name: send_mjpeg_stream()
# - Sends frames as: [4-byte length][JPEG bytes]
# - Perfect for ngrok TCP tunnels
# - Zero changes required in camera_ministry.py or main.py

import socket
import struct
import time
import traceback


def _connect(host, port, retry_delay=5):
    """
    Connects to the host's raw JPEG frame server.
    Retries forever until successful.
    """
    while True:
        try:
            print(f"[CameraRAW] Connecting to {host}:{port}")
            sock = socket.create_connection((host, port), timeout=10)
            print("[CameraRAW] Connection established")
            return sock
        except Exception as e:
            print(f"[CameraRAW] Connection failed: {e}")
            print(f"[CameraRAW] Retrying in {retry_delay}s")
            time.sleep(retry_delay)


def send_mjpeg_stream(host, port, frame_generator, retry_delay=5):
    """
    RAW JPEG uplink.
    NOTE: Name stays the same so camera_ministry.py does not change.
    Protocol:
        [4-byte big-endian length][JPEG bytes]
    """
    print(f"[CameraRAW] Starting RAW uplink → {host}:{port}")
    print("[CameraRAW] Protocol: [len][jpeg]")

    while True:
        sock = None
        try:
            sock = _connect(host, port, retry_delay)

            with sock:
                for jpeg_bytes in frame_generator:
                    try:
                        frame_size = len(jpeg_bytes)

                        # 4-byte big-endian length header
                        header = struct.pack(">I", frame_size)

                        send_start = time.time()

                        sock.sendall(header)
                        sock.sendall(jpeg_bytes)

                        send_time = (time.time() - send_start) * 1000
                        print(f"[CameraRAW] Sent frame ({frame_size} bytes) in {send_time:.2f} ms")

                    except Exception as e:
                        print(f"[CameraRAW] Frame send error: {e}")
                        traceback.print_exc()
                        print("[CameraRAW] Reconnecting…")
                        break

            print(f"[CameraRAW] Disconnected, retrying in {retry_delay}s")

        except Exception as e:
            print(f"[CameraRAW] Uplink error: {e}")
            traceback.print_exc()
            print(f"[CameraRAW] Will retry in {retry_delay}s")

        finally:
            if sock is not None:
                try:
                    sock.close()
                    print("[CameraRAW] Socket closed")
                except Exception:
                    print("[CameraRAW] Socket close failed")

            time.sleep(retry_delay)
