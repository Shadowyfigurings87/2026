# Rover1/ministries/camera/streamer.py
#
# Sovereign CameraBackend (final form)
# - True singleton Picamera2 instance
# - Thread-safe initialization
# - No double-start, no race conditions
# - Stable JPEG capture for unified uplink

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

    if not PICAMERA_AVAILABLE:
        raise RuntimeError("Picamera2 not available on this system")

    with _init_lock:
        if _picam is not None:
            return _picam

        try:
            time.sleep(1.0)  # warm-up for libcamera pipeline

            cam = Picamera2()

            config = cam.create_still_configuration(
                main={"size": resolution},
                transform=Transform(vflip=0, hflip=0),
                buffer_count=2,
            )

            cam.configure(config)
            cam.start()

            _picam = cam
            print("[CameraBackend] Picamera2 initialized (singleton)")

            return _picam

        except Exception as e:
            print(f"[CameraBackend] Camera init failed: {e}")
            raise RuntimeError("Camera init failed") from e


# ------------------------------------------------------------
# FRAME GENERATOR
# ------------------------------------------------------------
def camera_frame_generator(camera_fps=10, resolution=(640, 480), quality=90):
    """
    Yields JPEG frames at a controlled FPS.
    Uses the global singleton camera instance.
    """
    delay = 1.0 / max(camera_fps, 1)

    try:
        cam = get_camera(resolution=resolution, quality=quality)
    except Exception as e:
        print(f"[CameraBackend] Disabling camera stream: {e}")
        return

    while True:
        try:
            ts = time.time()

            # Capture raw frame
            frame = cam.capture_array()

            # Encode JPEG
            ret, jpeg = cv2.imencode(
                ".jpg",
                frame,
                [int(cv2.IMWRITE_JPEG_QUALITY), quality]
            )
            jpeg_bytes = jpeg.tobytes()

            yield {
                "ministry": "picamera2",
                "format": "jpeg",
                "ts": ts,
                "data": jpeg_bytes,
            }

        except Exception as e:
            print(f"[CameraBackend] Camera capture failed: {e}")
            return

        time.sleep(delay)
