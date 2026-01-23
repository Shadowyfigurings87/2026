# Rover1/ministries/ingestion/streams/redrover_stream.py

import time
import json
from queue import Queue, Empty

# Shared queue for RedRover JSONL lines
redrover_queue = Queue()


def push_redrover_line(line: str):
    """
    Called by the RedRover TCP server to enqueue a raw JSONL line.
    """
    redrover_queue.put(line)


def redrover_stream():
    """
    Generator consumed by merged_stream().
    Yields parsed RedRover events or None when idle.
    """
    while True:
        try:
            line = redrover_queue.get(timeout=0.01)
        except Empty:
            yield None
            continue

        # Parse JSON or fallback to raw event
        try:
            obj = json.loads(line)
        except Exception:
            obj = {
                "event": "raw",
                "raw": line,
                "ts": time.time(),
            }

        yield obj

