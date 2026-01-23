# ministries/ingestion/streams/arduino_stream.py

import time
from ministries.arduino.service import arduino_stream


def arduino_ingest_stream():
    """
    Wraps the Arduino ministry's arduino_stream() generator
    and emits ingestion-ready telemetry dicts.

    The Arduino ministry already:
      - reads serial in a background thread
      - parses HB / ACK / TEL / RAW lines
      - yields structured event dicts

    This wrapper simply normalizes them for the ingestion pipeline.
    """

    for event in arduino_stream():
        if not isinstance(event, dict):
            continue

        # Ensure ministry tag
        event.setdefault("ministry", "arduino")

        # Ensure timestamp
        event.setdefault("ts", time.time())

        # Ingestion pipeline expects ISO timestamp too
        event.setdefault("timestamp", time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))

        yield event
