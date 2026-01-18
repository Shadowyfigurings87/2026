import io
import time
from picamera2 import Picamera2


class CameraBackend:
    """
    Backend-only camera ministry.
    Produces JPEG frames for the unified uplink.
    Does NOT open sockets or send data.
    """

    def __init__(self, fps=10, size=(640, 480)):
        self.fps = fps
        self.frame_delay = 1.0 / fps

        self.picam = Picamera2()
        config = self.picam.create_video_configuration(
            main={"size": size}
        )
        self.picam.configure(config)
        self.picam.start()

    def frames(self):
        """
        Generator that yields:
        {
            "ministry": "picamera2",
            "format": "jpeg",
            "ts": <timestamp>,
            "data": <bytes>
        }
        """
        while True:
            buf = io.BytesIO()
            self.picam.capture_file(buf, format="jpeg")
            jpeg = buf.getvalue()

            yield {
                "ministry": "picamera2",
                "format": "jpeg",
                "ts": time.time(),
                "data": jpeg,
            }

            time.sleep(self.frame_delay)
