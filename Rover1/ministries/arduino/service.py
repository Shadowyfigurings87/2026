# ministries/arduino/service.py

import threading
import time

from .threads import arduino_reader_thread
from .state import latest_line
from .parser import parse_line


def start_arduino_ministry():
    """
    Launches the Arduino reader thread.
    The thread:
      - opens the serial port
      - reads raw lines
      - updates latest_line in state.py
    """
    t = threading.Thread(
        target=arduino_reader_thread,
        daemon=True,
        name="ArduinoReaderThread"
    )
    t.start()
    print("[Arduino] Ministry started (reader thread active)")


def arduino_stream():
    """
    Generator that yields parsed Arduino events.

    This is the bridge between:
      - the Arduino ministry (serial + parser)
      - the ingestion ministry (arduino_ingest_stream)
      - the uplink ministry (send_unified_uplink)

    It watches latest_line from state.py and emits structured
    event dicts whenever a new line arrives.
    """

    last_seen = None

    while True:
        line = latest_line

        if line and line != last_seen:
            last_seen = line

            # Parse into structured event
            event = parse_line(line)

            # Ensure event is a dict
            if isinstance(event, dict):

                # Ensure ministry tag
                event.setdefault("ministry", "arduino")

                # Ensure timestamp
                event.setdefault("ts", time.time())

                yield event

        time.sleep(0.01)
