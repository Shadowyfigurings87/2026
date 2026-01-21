# ingestion/streams/arduino_stream.py

import time
from ministries.arduino.state import latest_structured_event

def arduino_stream():
    """
    Yields structured Arduino events from the new modular Arduino ministry.
    """
    last_seen = None

    while True:
        evt = latest_structured_event()

        if evt and evt != last_seen:
            last_seen = evt

            yield {
                "ministry": "arduino",
                "event": evt.get("event"),
                "ts": evt.get("ts"),
                "raw": evt.get("raw"),
                "data": evt.get("data"),
                "latency": evt.get("latency"),
            }

        time.sleep(0.01)
