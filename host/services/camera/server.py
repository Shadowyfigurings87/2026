# host/services/camera/server.py
#
# RAW JPEG CAMERA SERVER + FPS TRACKING

import socket
import threading
import time
from host.logs.wrappers import log_ingest
from .frame_buffer import FrameBuffer

HOST = "0.0.0.0"
PORT = 5001

# Shared global buffer for latest frames
frame_buffer = FrameBuffer(max_frames=3)
print("SERVER BUFFER ID:", id(frame_buffer))

# Store timestamps of recent frames for FPS calculation
frame_times = []


def record_frame_timestamp():
    """Record arrival time of a frame and keep only recent timestamps."""
    now = time.time()
    frame_times.append(now)

    # Keep only the last ~60 timestamps (about 1–2 seconds of history)
    if len(frame_times) > 60:
        frame_times.pop(0)


def get_fps():
    """Return frames per second based on timestamps from the last 1 second."""
    now = time.time()
    one_sec_ago = now - 1.0
    return sum(1 for t in frame_times if t >= one_sec_ago)


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
    print(f"[CameraServer] === New connection from {addr} ===")
    log_ingest("camera_connection_open", addr=str(addr))

    try:
        with conn:
            while True:
                print("[CameraServer] Waiting for 4-byte frame length…")

                # Read 4-byte frame length
                length_bytes = conn.recv(4)

                if not length_bytes:
                    print("[CameraServer] No length bytes received — connection closed by client")
                    break

                if len(length_bytes) != 4:
                    print(f"[CameraServer] ERROR: Expected 4 bytes for length, got {len(length_bytes)}")
                    break

                frame_len = int.from_bytes(length_bytes, "big")
                print(f"[CameraServer] Incoming frame length: {frame_len} bytes")

                if frame_len <= 0 or frame_len > 10_000_000:
                    print(f"[CameraServer] ERROR: Invalid frame length: {frame_len}")
                    break

                # Read JPEG frame
                jpeg = b""
                bytes_remaining = frame_len

                print(f"[CameraServer] Reading JPEG frame ({frame_len} bytes)…")

                while len(jpeg) < frame_len:
                    chunk = conn.recv(bytes_remaining)

                    if not chunk:
                        print("[CameraServer] ERROR: Socket closed mid-frame")
                        break

                    jpeg += chunk
                    bytes_remaining -= len(chunk)

                    print(
                        f"[CameraServer]   Received chunk: {len(chunk)} bytes "
                        f"(total={len(jpeg)}/{frame_len})"
                    )

                if len(jpeg) != frame_len:
                    print(
                        f"[CameraServer] ERROR: Incomplete frame received "
                        f"({len(jpeg)}/{frame_len} bytes)"
                    )
                    break

                print(f"[CameraServer] Frame received successfully ({frame_len} bytes)")
                print("[CameraServer] Pushing frame into buffer…")

                # Store in buffer
                frame_buffer.push(jpeg)

                # Record timestamp for FPS calculation
                record_frame_timestamp()

                print("[CameraServer] Frame stored. Buffer size now:", len(frame_buffer.frames))
                print("[CameraServer] Waiting for next frame…\n")

    except Exception as e:
        print(f"[CameraServer] EXCEPTION: {e}")

    finally:
        print(f"[CameraServer] === Connection closed from {addr} ===")
        log_ingest("camera_connection_closed", addr=str(addr))


def start_camera_server():
    """
    Starts the camera server on port 5001.
    Accepts multiple connections, each handled in its own thread.
    """
    print("\n[CameraServer] =======================================")
    print("[CameraServer] Starting RAW JPEG camera server…")
    print(f"[CameraServer] Binding to {HOST}:{PORT}")
    print("[CameraServer] =======================================\n")

    log_ingest("camera_server_start", host=HOST, port=PORT)

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    try:
        sock.bind((HOST, PORT))
    except Exception as e:
        print(f"[CameraServer] ERROR: Failed to bind to {HOST}:{PORT} — {e}")
        raise

    sock.listen(5)

    print(f"[CameraServer] Listening on {HOST}:{PORT}")
    log_ingest("camera_server_listening", host=HOST, port=PORT)

    while True:
        print("[CameraServer] Waiting for incoming connection…")
        conn, addr = sock.accept()
        print(f"[CameraServer] Accepted connection from {addr}")

        threading.Thread(
            target=handle_camera_connection,
            args=(conn, addr),
            daemon=True,
        ).start()
