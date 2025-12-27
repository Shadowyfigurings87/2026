import time
from picamera2 import Picamera2
from ministries.utils.jsonl import encode_jsonl


def init_camera():
    """Initialize Pi Camera Module 3 using Picamera2 (Bookworm standard)."""
    cam = Picamera2()

    config = cam.create_video_configuration(
        main={"size": (1280, 720)},  # scalable resolution
        controls={
            "FrameDurationLimits": (33333, 33333),  # ~30 FPS
        }
    )

    cam.configure(config)
    cam.start()

    return cam


def capture_metadata(cam):
    """Capture metadata only (no image data) for lightweight streaming."""
    meta = cam.capture_metadata()

    return {
        "ministry": "camera",
        "ts": time.time(),
        "exposure": meta.get("ExposureTime"),
        "gain": meta.get("AnalogueGain"),
        "awb": meta.get("ColourGains"),
        "focus": meta.get("LensPosition"),
        "brightness": meta.get("Brightness"),
        "temperature": meta.get("SensorTemperature"),
    }


def main():
    cam = None

    while True:
        try:
            if cam is None:
                cam = init_camera()
                print("[camera] initialized", flush=True)

            obj = capture_metadata(cam)

            # Output JSONL to stdout for dashboard supervisor
            print(encode_jsonl(obj), end="", flush=True)

            # Adjust metadata frequency (10 Hz)
            time.sleep(0.1)

        except Exception as e:
            print(f"[camera] error: {e}", flush=True)
            time.sleep(1)
            cam = None  # force re-init


if __name__ == "__main__":
    main()
