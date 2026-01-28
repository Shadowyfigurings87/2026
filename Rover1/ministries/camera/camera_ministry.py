# Rover1/ministries/camera/camera_ministry.py

import threading
import time

from Rover1.ministries.camera.config import (
    RESOLUTION,
    QUALITY,
    FPS,
    HEALTH_INTERVAL,
    HOST,
    PORT,
    CONNECT_RETRY_DELAY,
)
from Rover1.ministries.camera.camera_backend import get_camera
from Rover1.ministries.camera.encoder import encode_jpeg
from Rover1.ministries.camera.buffer import FrameBuffer
from Rover1.ministries.camera.mjpeg_client import send_mjpeg_stream   # RAW JPEG uplink


_buffer = FrameBuffer(size=3)


def _capture_loop():
    print("[CameraMinistry] Capture loop starting…")
    print(f"[CameraMinistry] Config: RESOLUTION={RESOLUTION}, FPS={FPS}")

    try:
        print("[CameraMinistry] Initializing camera backend…")
        cam = get_camera(resolution=RESOLUTION)
        print("[CameraMinistry] Camera backend ready")
    except Exception as e:
        print(f"[CameraMinistry] Camera unavailable: {e}")
        return

    delay = 1.0 / max(FPS, 1)
    print(f"[CameraMinistry] Capture delay per frame: {delay:.4f}s")

    while True:
        loop_start = time.time()

        try:
            cap_start = time.time()
            frame = cam.capture_array()
            cap_time = (time.time() - cap_start) * 1000
            print(f"[CameraMinistry] Frame captured ({cap_time:.2f} ms)")
        except Exception as e:
            print(f"[CameraMinistry] Capture error: {e}")
            time.sleep(1)
            continue

        try:
            _buffer.push(frame)
            print("[CameraMinistry] Frame pushed to buffer")
        except Exception as e:
            print(f"[CameraMinistry] Buffer push error: {e}")

        loop_time = time.time() - loop_start
        sleep_left = delay - loop_time
        print(f"[CameraMinistry] Loop time={loop_time*1000:.2f} ms, sleep={max(sleep_left,0)*1000:.2f} ms")

        if sleep_left > 0:
            time.sleep(sleep_left)


def _jpeg_generator():
    print("[CameraMinistry] JPEG generator starting…")
    print(f"[CameraMinistry] JPEG quality={QUALITY}")

    last_health = time.time()
    frames_sent = 0

    while True:
        frame = _buffer.latest()
        if frame is None:
            print("[CameraMinistry] No frame in buffer, waiting…")
            time.sleep(0.01)
            continue

        try:
            enc_start = time.time()
            jpeg = encode_jpeg(frame, quality=QUALITY)
            enc_time = (time.time() - enc_start) * 1000
            print(f"[CameraMinistry] JPEG encoded ({enc_time:.2f} ms)")
            yield jpeg
            frames_sent += 1
        except Exception as e:
            print(f"[CameraMinistry] Encode error: {e}")
            time.sleep(0.1)

        now = time.time()
        if now - last_health > HEALTH_INTERVAL:
            fps = frames_sent / HEALTH_INTERVAL
            print(f"[CameraHealth] fps={fps:.1f} (frames_sent={frames_sent})")
            frames_sent = 0
            last_health = now


def _run_camera_ministry():
    print("[CameraMinistry] Starting camera ministry…")
    print(f"[CameraMinistry] Target uplink: {HOST}:{PORT}")

    # Start capture loop
    threading.Thread(
        target=_capture_loop,
        name="CameraCapture",
        daemon=True,
    ).start()
    print("[CameraMinistry] Capture thread started")

    # Directly start RAW uplink (blocking inside this thread)
    print("[CameraMinistry] Launching RAW uplink client…")
    send_mjpeg_stream(
        host=HOST,
        port=PORT,
        frame_generator=_jpeg_generator(),   # original behavior
        retry_delay=CONNECT_RETRY_DELAY,
    )


def start_camera_ministry():
    print("[CameraMinistry] Bootstrapping ministry thread…")
    t = threading.Thread(
        target=_run_camera_ministry,
        name="CameraMinistry",
        daemon=True,
    )
    t.start()
    print("[CameraMinistry] Thread started successfully")
