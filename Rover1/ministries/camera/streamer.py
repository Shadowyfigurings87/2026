# Rover1/ministries/camera/streamer.py
#
# Hardened CameraBackend-only module.
# - Lazy initialization (only on first frame)
# - Warm-up delay
# - One init attempt only
# - Telemetry-only fallback
# - No MJPEG, no sockets, no legacy code

import time

try:
    from picamera2 import Picamera2
    from libcamera import Transform
    PICAMERA_AVAILABLE = True
except Exception as e:
    print(f"[CameraBackend] Picamera2 import failed: {e}")
    PICAMERA_AVAILABLE = False


class CameraBackend:
    """
    Minimal backend-only camera module.
    Initializes Picamera2 lazily on first frame request.
    If init fails once, camera is permanently disabled.
    """

    def __init__(self, resolution=(640, 480), quality=90):
        self.resolution = resolution
        self.quality = quality
        self.picam = None
        self.initialized = False
        self.failed = False

    def _ensure_init(self):
        if self.failed:
            raise RuntimeError("Camera init previously failed")

        if self.initialized:
            return

        if not PICAMERA_AVAILABLE:
            self.failed = True
            raise RuntimeError("Picamera2 not available on this system")

        try:
            # Warm-up delay for libcamera pipeline
            time.sleep(1.0)

            picam = Picamera2()

            config = picam.create_still_configuration(
                main={"size": self.resolution},
                transform=Transform(vflip=0, hflip=0),
                buffer_count=2,
            )

            picam.configure(config)
            picam.start()

            self.picam = picam
            self.initialized = True
            print("[CameraBackend] Picamera2 initialized")

        except Exception as e:
            self.failed = True
            print(f"[CameraBackend] Camera init sequence did not complete: {e}")
            raise RuntimeError("Camera init sequence did not complete") from e

    def get_frame(self):
        """
        Capture a JPEG frame and return:
        {
            "ministry": "picamera2",
            "format": "jpeg",
            "ts": <float>,
            "data": <bytes>
        }
        """
        self._ensure_init()

        ts = time.time()
        jpeg_bytes = self.picam.capture_buffer(
            "main",
            format="jpeg",
            quality=self.quality,
        )

        return {
            "ministry": "picamera2",
            "format": "jpeg",
            "ts": ts,
            "data": jpeg_bytes,
        }


def camera_frame_generator(camera_fps=10):
    """
    Generator that yields JPEG frames at a controlled FPS.
    If camera init fails, generator stops permanently.
    """
    backend = CameraBackend()
    delay = 1.0 / max(camera_fps, 1)

    while True:
        try:
            frame = backend.get_frame()
        except Exception as e:
            print(f"[CameraBackend] Disabling camera stream: {e}")
            return  # Stop yielding frames forever

        yield frame
        time.sleep(delay)
