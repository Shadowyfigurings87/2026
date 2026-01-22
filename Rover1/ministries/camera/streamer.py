# Rover1/ministries/camera/streamer.py
#
# Sovereign CameraBackend (dual-uplink version)
# - True singleton Picamera2 instance
# - Thread-safe initialization
# - Stable JPEG capture for MJPEG uplink
# - Raw JPEG bytes output (NOT dicts)
# - Full debug instrumentation

import time
import threading
import cv2

try:
    from picamera2 import Picamera2
    from libcamera import Transform
    PICAMERA_AVAILABLE = True
except Exception as e:
    print(f"[CameraBackend] Picamera2 import failed: {e}")
    PICAMERA_AVAILABLE = False


# ------------------------------------------------------------
# GLOBAL SINGLETON CAMERA INSTANCE
# ------------------------------------------------------------
_picam = None
_init_lock = threading.Lock()


def get_camera(resolution=(640, 480), quality=90):
    """
    Returns the global Picamera2 instance.
    Initializes it once, safely, on first call.
    """
    global _picam

    print("[CameraBackend] get_camera() called")

    if not PICAMERA_AVAILABLE:
        raise RuntimeError("Picamera2 not available on this system")

    with _init_lock:
        if _picam is not None:
            print("[CameraBackend] Returning existing singleton camera")
            return _picam

        try:
            print("[CameraBackend] Initializing Picamera2…")
            time.sleep(1.0)  # warm-up for libcamera pipeline

            cam = Picamera2()

            config = cam.create_still_configuration(
                main={"size": resolution},
                transform=Transform(vflip=0, hflip=0),
                buffer_count=2,
            )

            print(f"[CameraBackend] Applying config: {resolution}")
            cam.configure(config)
            cam.start()

            _picam = cam
            print("[CameraBackend] Picamera2 initialized (singleton)")

            return _picam

        except Exception as e:
            print(f"[CameraBackend] Camera init failed: {e}")
            raise RuntimeError("Camera init failed") from e


# ------------------------------------------------------------
# FRAME GENERATOR (raw JPEG bytes)
# ------------------------------------------------------------
def camera_frame_generator(camera_fps=10, resolution=(640, 480), quality=90):
    """
    Yields raw JPEG bytes at a controlled FPS.
    Designed for MJPEG uplink.
    """
    print(f"[CameraBackend] Starting frame generator: {camera_fps} FPS, {resolution}, Q={quality}")

    delay = 1.0 / max(camera_fps, 1)

    try:
        cam = get_camera(resolution=resolution, quality=quality)
    except Exception as e:
        print(f"[CameraBackend] Disabling camera stream: {e}")
        return

    frames = 0
    last_fps_time = time.time()

    while True:
        loop_start = time.time()

        try:
            # Capture
            cap_start = time.time()
            frame = cam.capture_array()
            cap_time = time.time() - cap_start
            print(f"[CameraBackend] Capture OK ({cap_time*1000:.2f} ms)")

            # Encode
            enc_start = time.time()
            ret, jpeg = cv2.imencode(
                ".jpg",
                frame,
                [int(cv2.IMWRITE_JPEG_QUALITY), quality]
            )
            jpeg_bytes = jpeg.tobytes()
            enc_time = time.time() - enc_start
            print(f"[CameraBackend] Encode OK ({enc_time*1000:.2f} ms)")

            frames += 1

            # FPS debug
            now = time.time()
            if now - last_fps_time >= 1.0:
                print(f"[CameraBackend] FPS={frames}")
                frames = 0
                last_fps_time = now

