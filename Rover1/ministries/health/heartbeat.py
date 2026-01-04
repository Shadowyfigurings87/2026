import time

def heartbeat_stream(interval=5):
    """Emit a heartbeat JSON object every <interval> seconds."""
    while True:
        yield {
            "ministry": "heartbeat",
            "ts": time.time(),
            "status": "alive"
        }
        time.sleep(interval)
