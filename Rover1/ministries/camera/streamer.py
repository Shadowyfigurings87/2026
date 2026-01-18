# Rover1/ministries/camera/streamer.py
#
# Clean CameraBackend-only module.
# No MJPEG streamer, no sockets, no legacy code.
# Provides a simple generator that yields JPEG frames
# for the unified uplink.

import time
from picamera2 import Picamera2
from libcamera import Transform


class CameraBackend:
    """
    Minimal backend-only camera module.
    Initializes Picamera2 once and provides JPEG frames
    via get_frame() for the unified uplink.
    """

    def __init__(self, resolution=(640, 480), quality=90):
        self.picam = Picamera2()

        config = self.picam.create_still_configuration(
            main={"size": resolution},
            transform=Transform(vflip=0, hflip=0),
            buffer_count=2,
        )

        self.picam.configure(config)
        self.picam.start()

        self.quality = quality
        self.last_frame_ts = 0.0

        print("[CameraBackend] Picamera2 initialized")

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
        ts = time.time()
        jpeg_bytes = self.picam.capture_buffer("main", format="jpeg", quality=self.quality)

        return {
            "ministry": "picamera2",
            "format": "jpeg",
            "ts": ts,
            "data": jpeg_bytes,
        }


def camera_frame_generator(camera_fps=10):
    """
    Generator that yields JPEG frames at a controlled FPS.
    Used by unified_stream_with_camera().
    """
    cam = CameraBackend()
    delay = 1.0 / max(camera_fps, 1)

    while True:
        frame = cam.get_frame()
        yield frame
        time.sleep(delay)
