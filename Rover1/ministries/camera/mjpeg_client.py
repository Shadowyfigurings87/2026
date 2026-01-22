# Rover1/ministries/camera/mjpeg_client.py
#
# Hardened MJPEG uplink client with full debug instrumentation.
# - Clear connection lifecycle logs
# - Per-frame timing + byte size
# - Robust error handling
# - Clean boundary formatting
# - Safe reconnect loop

import socket
import time
import traceback


def connect_mjpeg(host, port, retry_delay=5):
    """
    Attempts to connect to the host MJPEG server.
    Retries forever with delay.
    """
    while True:
        try:
            print(f"[CameraMJPEG] Attempting connection to {host}:{port}")
            sock = socket.create_connection((host, port), timeout=10)
            print("[CameraMJPEG] Connection established")
            return sock
        except Exception as e:
            print(f"[CameraMJPEG] Connection failed: {e}")
            print(f"[CameraMJPEG] Retrying in {retry_delay}s")
            time.sleep(retry_delay)


def send_mjpeg_stream(host, port, frame_generator, retry_delay=5, path="/mjpeg"):
    """
    Sends JPEG frames as MJPEG over HTTP.
    frame_generator must yield raw JPEG bytes.
    """
    boundary = b"frame"  # boundary name (no leading --)
    print(f"[CameraMJPEG] Starting MJPEG uplink → {host}:{port}{path}")
    print(f"[CameraMJPEG] Using boundary: {boundary}")

    while True:
        sock = None
        try:
            sock = connect_mjpeg(host, port, retry_delay=retry_delay)

            with sock:
                # Build HTTP header
                header = (
                    f"POST {path} HTTP/1.1\r\n"
                    f"Host: {host}\r\n"
                    f"Content-Type: multipart/x-mixed-replace; boundary={boundary.decode()}\r\n"
                    f"Connection: keep-alive\r\n"
                    f"\r\n"
                ).encode("ascii")

                print("[CameraMJPEG] Sending HTTP header…")
                sock.sendall(header)
                print("[CameraMJPEG] Header sent successfully")

                # Frame loop
                for jpeg_bytes in frame_generator:
                    try:
                        frame_size = len(jpeg_bytes)
                        print(f"[CameraMJPEG] Sending frame ({frame_size} bytes)…")

                        send_start = time.time()

                        part = (
                            b"--" + boundary + b"\r\n"
                            + b"Content-Type: image/jpeg\r\n"
                            + b"Content-Length: " + str(frame_size).encode("ascii") + b"\r\n"
                            + b"\r\n"
                            + jpeg_bytes + b"\r\n"
                        )

                        sock.sendall(part)

                        send_time = (time.time() - send_start) * 1000
                        print(f"[CameraMJPEG] Frame sent ({send_time:.2f} ms)")

                    except Exception as e:
                        print(f"[CameraMJPEG] Frame send error: {e}")
                        traceback.print_exc()
                        print("[CameraMJPEG] Breaking frame loop to reconnect…")
                        break

            print(f"[CameraMJPEG] Disconnected from server, retrying in {retry_delay}s")

        except Exception as e:
            print(f"[CameraMJPEG] Uplink error: {e}")
            traceback.print_exc()
            print(f"[CameraMJPEG] Will retry in {retry_delay}s")

        finally:
            if sock is not None:
                try:
                    sock.close()
                    print("[CameraMJPEG] Socket closed cleanly")
                except Exception:
                    print("[CameraMJPEG] Socket close failed")

            time.sleep(retry_delay)
