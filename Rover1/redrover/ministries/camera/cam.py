from ministries.utils.jsonl import now_ts

def camera_stream():
    """
    Placeholder: emit fake frames for now.
    Replace with real camera capture later.
    """
    frame_id = 0
    while True:
        yield {
            "kind": "telemetry",
            "source": "camera",
            "rover": "RedRover",
            "ts": now_ts(),
            "data": {
                "frame_id": frame_id
            }
        }
        frame_id += 1
        # tune rate as needed
        import time
        time.sleep(0.1)
