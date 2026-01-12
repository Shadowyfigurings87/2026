# ministries/camera/camera.py

import time
import base64
import cv2  # pip install opencv-python


def camera_stream(device_index=0, fps=5):
    """
    Yield camera frames as JSON objects suitable for host ingestion.

    Fields:
      - ministry: "picamera2"
      - ts: float (epoch seconds)
      - frame: base64-encoded JPEG
      - format: "jpeg"
      - device: "picamera2"
    """
    cap = cv2.VideoCapture(device_index)

    if not cap.isOpened():
        raise RuntimeError(f"Camera device {device_index} could not be opened")

    delay = 1.0 / fps

    while True:
        ret, frame = cap.read()
        if not ret:
            # Skip if frame not captured
            time.sleep(delay)
            continue

        # Encode frame as JPEG
        success, jpeg = cv2.imencode(".jpg", frame)
        if not success:
            time.sleep(delay)
            continue

        # Convert to base64 string
        b64 = base64.b64encode(jpeg.tobytes()).decode("utf-8")

        yield {
            "ministry": "picamera2",
            "ts": time.time(),
            "frame": b64,              # <-- matches host ingestion
            "format": "jpeg",
            "device": "picamera2",     # <-- string, consistent with host
        }

        time.sleep(delay)
