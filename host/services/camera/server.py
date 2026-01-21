# host/services/camera/server.py
#
# Dedicated camera ingestion server
# Listens on port 5001
# Receives raw JPEG frames from Rover1
# Stores them in a shared frame buffer for cockpit/UI access

import socket
import threading
from host.logs.wrappers import log_ingest
from .frame_buffer import FrameBuffer

HOST = "0.0.0.0"
PORT = 5001

# Shared global buffer for latest frames
frame_buffer = FrameBuffer(max_frames=3)


def handle_camera_connection(conn, addr):
    """
    Handles a single camera connection from Rover1.

    Protocol:
        <4-byte big-endian length>
        <jpeg bytes>
        <4-byte length>
        <jpeg bytes>
        ...
    """
    log_ingest("camera_connection_open", addr=str(addr))

    try:
        with conn:
            while True:
                # Read 4-byte frame length
                length_bytes = conn.recv(4)
                if not length_bytes:
                    break

                frame_len = int.from_bytes(length_bytes, "big")

                # Read JPEG frame
                jpeg = b""
                while len(jpeg) < frame_len:
                    chunk = conn.recv(frame_len - len(jpeg))
                    if not chunk:
                        break
                    jpeg += chunk

                if len(jpeg) != frame_len:
                    print("[CameraServer] Incomplete frame received")
                    break

                # Store in buffer
                frame_buffer.push(jpeg)

    except Exception as e:
        print(f"[CameraServer] Error: {e}")

    finally:
        log_ingest("camera_connection_closed", addr=str(addr))


def start_camera_server():
    """
    Starts the camera server on port 5001.
    Accepts multiple connections, each handled in its own thread.
    """
    log_ingest("camera_server_start", host=HOST, port=PORT)

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind((HOST, PORT))
    sock.listen(5)

    log_ingest("camera_server_listening", host=HOST, port=PORT)

    while True:
        conn, addr = sock.accept()
        threading.Thread(
            target=handle_camera_connection,
            args=(conn, addr),
            daemon=True,
        ).start()
