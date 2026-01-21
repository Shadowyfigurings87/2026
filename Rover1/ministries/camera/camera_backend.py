import time
import threading

try:
    from picamera2 import Picamera2
    from libcamera import Transform
    PICAMERA_AVAILABLE = True
except Exception as e:
    print(f"[CameraBackend] Picamera2 import failed: {e}")
    PICAMERA_AVAILABLE = False

_picam = None
_init_lock = threading.Lock()


def get_camera(resolution=(640, 480)):
    global _picam

    if not PICAMERA_AVAILABLE:
        raise RuntimeError("Picamera2 not available")

    with _init_lock:
        if _picam is not None:
            return _picam

        try:
            time.sleep(1.0)

            cam = Picamera2()
            config = cam.create_video_configuration(
                main={"size": resolution},
                transform=Transform(vflip=0, hflip=0),
                buffer_count=4,
            )
            cam.configure(config)
            cam.start()

            _picam = cam
            print("[CameraBackend] Picamera2 initialized")
            return _picam

        except Exception as e:
            print(f"[CameraBackend] Camera init failed: {e}")
            raise
