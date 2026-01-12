# ministries/camera/camera.py

import time
import base64
from picamera2 import Picamera2

def camera_stream(fps=5):
    """
    Original working Picamera2 camera ministry.
    Produces JSON aligned with host ingestion.
    """

    picam = Picamera2()
    config = picam.create_still_configuration()
    picam.configure(config)
    picam.start()

    delay = 1.0 / fps

    while True:
        frame = picam.capture_array()

        # Encode JPEG
        import cv2
        success, jpeg = cv2.imencode(".jpg", frame)
        if not success:
            time.sleep(delay)
            continue

        b64 = base64.b64encode(jpeg.tobytes()).decode("utf-8")

        yield {
            "ministry": "picamera2",
            "ts": time.time(),
            "frame": b64,
            "format": "jpeg",
            "device": "picamera2",
        }

        time.sleep(delay)
