import time
import base64
import cv2  # OpenCV (install with pip install opencv-python)

def camera_stream(device_index=0, fps=5):
    """
    Yield camera frames as JSON objects.
    Encodes frames as base64 JPEG for transport.
    """
    cap = cv2.VideoCapture(device_index)

    if not cap.isOpened():
        raise RuntimeError(f"Camera device {device_index} could not be opened")

    delay = 1.0 / fps

    while True:
        ret, frame = cap.read()
        if not ret:
            continue

        # Encode frame as JPEG
        success, jpeg = cv2.imencode(".jpg", frame)
        if not success:
            continue

        # Convert to base64 string
        b64 = base64.b64encode(jpeg.tobytes()).decode("utf-8")

        yield {
            "ministry": "picamera2",
            "ts": time.time(),
            "frame": b64,          # <-- FIXED
            "format": "jpeg",
            "device": "picamera2", # <-- FIXED
        }

        time.sleep(delay)
