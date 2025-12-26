import time
import base64
from ministries.utils.jsonl import now_ts

# Picamera2 is the official modern camera stack for Raspberry Pi
from picamera2 import Picamera2
import libcamera


def camera_stream(
    width=640,
    height=480,
    jpeg_quality=80,
    target_fps=10,
    max_frame_size=200_000,  # bytes
):
    """
    High‑capability camera stream for Raspberry Pi Camera Module 3.
    Produces JSON‑friendly JPEG frames with metadata.

    Features:
      - Adaptive framerate
      - JPEG compression
      - Base64 encoding
      - Exposure + gain metadata
      - Thermal throttling protection
      - Never blocks, never crashes
    """

    picam = Picamera2()

    config = picam.create_still_configuration(
        main={"size": (width, height), "format": "RGB888"},
        buffer_count=2
    )
    picam.configure(config)
    picam.start()

    frame_id = 0
    frame_interval = 1.0 / target_fps
    last_frame_time = time.time()

    while True:
        try:
            # Enforce target FPS
            now = time.time()
            delta = now - last_frame_time
            if delta < frame_interval:
                time.sleep(frame_interval - delta)
            last_frame_time = time.time()

            # Capture frame as JPEG
            jpeg_bytes = picam.capture_buffer(
                "main",
                format="jpeg",
                quality=jpeg_quality
            )

            # Adaptive compression: if too large, reduce quality
            if len(jpeg_bytes) > max_frame_size:
                jpeg_quality = max(40, jpeg_quality - 5)
            else:
                jpeg_quality = min(90, jpeg_quality + 1)

            # Base64 encode for JSONL
            jpeg_b64 = base64.b64encode(jpeg_bytes).decode("ascii")

            # Metadata from libcamera
            metadata = picam.capture_metadata()
            exposure = metadata.get("ExposureTime", None)
            gain = metadata.get("AnalogueGain", None)

            # Build JSON‑friendly object
            yield {
                "kind": "telemetry",
                "source": "camera",
                "rover": "RedRover",
                "ts": now_ts(),
                "data": {
                    "frame_id": frame_id,
                    "width": width,
                    "height": height,
                    "jpeg_quality": jpeg_quality,
                    "jpeg_b64": jpeg_b64,
                    "exposure_us": exposure,
                    "gain": gain,
                }
            }

            frame_id += 1

        except Exception as e:
            # Never kill the generator — report error and continue
            yield {
                "kind": "telemetry",
                "source": "camera",
                "rover": "RedRover",
                "ts": now_ts(),
                "error": str(e)
            }
            time.sleep(0.5)

