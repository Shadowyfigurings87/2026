# Rover1/ministries/camera/streamer.py
#
# Unified camera streamer for Rover1
# - Uses camera_backend.get_camera() for capture
# - Uses encoder.encode_jpeg() for JPEG encoding
# - Yields raw JPEG bytes for uplink
# - Designed to plug directly into send_mjpeg_stream() (now raw)

import time

from Rover1.ministries.camera.camera_backend import get_camera
from Rover1.ministries.camera.encoder import encode_jpeg
from Rover1.ministries.config import RESOLUTION, QUALITY, FPS, HEALTH_INTERVAL


def camera_frame_generator(
    camera_fps: int = None,
    resolution=None,
    quality: int = None,
):
    """
    Yields raw JPEG bytes at a controlled FPS.
    Uses the same config values as camera_ministry.
    """
    if camera_fps is None:
        camera_fps = FPS
    if resolution is None:
        resolution = RESOLUTION
    if quality is None:
        quality = QUALITY

    print(
        f"[Streamer] Starting frame generator: "
        f"{camera_fps} FPS, res={resolution}, Q={quality}"
    )

    delay = 1.0 / max(camera_fps, 1)

    try:
        cam = get_camera(resolution=resolution)
        print("[Streamer] Camera acquired from backend")
    except Exception as e:
        print(f"[Streamer] Camera unavailable: {e}")
        return

    frames = 0
    last_health = time.time()

    while True:
        loop_start = time.time()

        # Capture
        try:
            cap_start = time.time()
            frame = cam.capture_array()
            cap_time = (time.time() - cap_start) * 1000
            print(f"[Streamer] Capture OK ({cap_time:.2f} ms)")
        except Exception as e:
            print(f"[Streamer] Capture error: {e}")
            time.sleep(0.5)
            continue

        # Encode
        try:
            enc_start = time.time()
            jpeg_bytes = encode_jpeg(frame, quality=quality)
            enc_time = (time.time() - enc_start) * 1000
            print(f"[Streamer] Encode OK ({enc_time:.2f} ms)")
        except Exception as e:
            print(f"[Streamer] Encode error: {e}")
            time.sleep(0.1)
            continue

        frames += 1
        yield jpeg_bytes

        # Health metrics
        now = time.time()
        if now - last_health >= HEALTH_INTERVAL:
            fps_measured = frames / (now - last_health)
            print(f"[StreamerHealth] fps={fps_measured:.1f} (frames={frames})")
            frames = 0
            last_health = now

        # FPS pacing
        loop_time = time.time() - loop_start
        sleep_left = delay - loop_time
        if sleep_left > 0:
            time.sleep(sleep_left)
