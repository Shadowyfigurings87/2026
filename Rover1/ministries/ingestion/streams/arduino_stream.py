# ministries/ingestion/streams/arduino_stream.py

import time
from ministries.arduino.service import arduino_stream

def arduino_ingest_stream():
    """
    Wraps the Arduino ministry's arduino_stream() generator
    and emits ingestion-ready telemetry dicts.
    """
    for event in arduino_stream():
        if not isinstance(event, dict):
            continue

        # Ensure ministry tag
        event.setdefault("ministry", "arduino")

        # Ensure timestamp
        event.setdefault("ts", time.time())

        yield event
