# Rover1/ministries/camera/camera_ministry.py

import threading
import time

from .config import RESOLUTION, QUALITY, FPS, HEALTH_INTERVAL, HOST, PORT, CONNECT_RETRY_DELAY
from .camera_backend import get_camera
from .encoder import encode_jpeg
from .buffer import FrameBuffer
from .mjpeg_client import send_mjpeg_stream


_buffer = FrameBuffer(size=3)


def _capture_loop():
    try:
        cam = get_camera(resolution=RESOLUTION)
    except Exception as e:
        print(f"[CameraMinistry] Camera unavailable: {e}")
        return

    delay = 1.0 / max(FPS, 1)

    while True:
        ts = time.time()
        try:
            frame = cam.capture_array()
            _buffer.push(frame)
        except Exception as e:
            print(f"[CameraMinistry] Capture error: {e}")
            time.sleep(1)
            continue

        sleep_left = delay - (time.time() - ts)
        if sleep_left > 0:
            time.sleep(sleep_left)


def _jpeg_generator():
    last_health = time.time()
    frames_sent = 0

    while True:
        frame = _buffer.latest()
        if frame is None:
            time.sleep(0.01)
            continue

        try:
            jpeg = encode_jpeg(frame, quality=QUALITY)
            yield jpeg
            frames_sent += 1
        except Exception as e:
            print(f"[CameraMinistry] Encode error: {e}")
            time.sleep(0.1)

        now = time.time()
        if now - last_health > HEALTH_INTERVAL:
            fps = frames_sent / HEALTH_INTERVAL
            print(f"[CameraHealth] fps={fps:.1f}")
            frames_sent = 0
            last_health = now


def _run_camera_ministry():
    print("[CameraMinistry] Starting capture loop…")
    threading.Thread(
        target=_capture_loop,
        name="CameraCapture",
        daemon=True,
    ).start()

    print(f"[CameraMinistry] Starting MJPEG client to {HOST}:{PORT}…")
    send_mjpeg_stream(
        host=HOST,
        port=PORT,
        frame_generator=_jpeg_generator(),
        retry_delay=CONNECT_RETRY_DELAY,
    )


def start_camera_ministry():
    t = threading.Thread(
        target=_run_camera_ministry,
        name="CameraMinistry",
        daemon=True,
    )
    t.start()
    print("[CameraMinistry] Thread started")
