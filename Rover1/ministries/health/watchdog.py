import time

def watchdog_stream(check_interval=3):
    """
    Emit watchdog alerts if ministries appear stalled.
    For now, this is a placeholder that always reports healthy.
    """
    while True:
        yield {
            "ministry": "watchdog",
            "ts": time.time(),
            "status": "ok"
        }
        time.sleep(check_interval)
