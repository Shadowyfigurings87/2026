# Rover1/ministries/camera/mjpeg_client.py
#
# Connects to host MJPEG server and pushes JPEG frames.

import socket
import time


def connect_mjpeg(host, port, retry_delay=5):
    while True:
        try:
            print(f"[CameraMJPEG] Connecting to {host}:{port}…")
            sock = socket.create_connection((host, port), timeout=10)
            print("[CameraMJPEG] Connected")
            return sock
        except Exception as e:
            print(f"[CameraMJPEG] Connection failed: {e}")
            print(f"[CameraMJPEG] Retrying in {retry_delay}s")
            time.sleep(retry_delay)


def send_mjpeg_stream(host, port, frame_generator, retry_delay=5):
    """
    Connects to host and sends frames as MJPEG over HTTP.
    frame_generator must yield JPEG bytes.
    """
    boundary = b"--frame"

    while True:
        sock = None
        try:
            sock = connect_mjpeg(host, port, retry_delay=retry_delay)
            with sock:
                # Basic HTTP header for MJPEG push (if server expects it)
                header = (
                    b"POST /mjpeg HTTP/1.1\r\n"
                    b"Host: camera\r\n"
                    b"Content-Type: multipart/x-mixed-replace; boundary=frame\r\n"
                    b"\r\n"
                )
                sock.sendall(header)

                for jpeg_bytes in frame_generator:
                    try:
                        part = (
                            boundary + b"\r\n"
                            + b"Content-Type: image/jpeg\r\n"
                            + b"Content-Length: " + str(len(jpeg_bytes)).encode("ascii") + b"\r\n"
                            + b"\r\n"
                            + jpeg_bytes + b"\r\n"
                        )
                        sock.sendall(part)
                    except Exception as e:
                        print(f"[CameraMJPEG] Send error: {e}")
                        break

            print(f"[CameraMJPEG] Disconnected, retrying in {retry_delay}s")

        except Exception as e:
            print(f"[CameraMJPEG] Error: {e}, retrying in {retry_delay}s")

        finally:
            if sock is not None:
                try:
                    sock.close()
                except Exception:
                    pass
            time.sleep(retry_delay)
