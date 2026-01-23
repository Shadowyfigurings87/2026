# ministries/arduino/service.py

import threading
import time

from ministries.arduino.threads import arduino_reader_thread
from ministries.arduino import state
from ministries.arduino.parser import parse_line

print(f"[Arduino] service.py loaded from: {__file__}")

# ---------------------------------------------------------
# Readiness flag (set by threads.py when serial opens)
# ---------------------------------------------------------
arduino_ready = False

def mark_arduino_ready():
    global arduino_ready
    arduino_ready = True


def start_arduino_ministry():
    print("[Arduino] Starting ministry… launching reader thread")

    t = threading.Thread(
        target=arduino_reader_thread,
        daemon=True,
        name="ArduinoReaderThread",
    )
    t.start()

    print("[Arduino] Ministry started (reader thread active)")


def arduino_stream(poll_interval: float = 0.01):
    print("[Arduino] arduino_stream() generator starting…")
    last_seen = None
    idle_counter = 0

    while True:
        line = state.latest_line

        if not line:
            idle_counter += 1
            if idle_counter % 200 == 0:
                print("[Arduino] Waiting for first line… (idle)")
            time.sleep(poll_interval)
            continue

        if line is not last_seen:
            print(f"[Arduino] New line detected: {line!r}")
            last_seen = line

            try:
                print(f"[Arduino] Parsing line: {line!r}")
                event = parse_line(line)
                print(f"[Arduino] Parsed event: {event}")
            except Exception as e:
                print(f"[Arduino] Parse error for line {line!r}: {e}")
                event = {"event": "raw", "raw": line, "ts": time.time()}

            if not isinstance(event, dict):
                print(f"[Arduino] WARNING: Parsed event is not a dict: {event!r}")
                event = {"event": "raw", "raw": line, "ts": time.time()}

            event.setdefault("ministry", "arduino")
            event.setdefault("ts", time.time())

            print(f"[Arduino] Yielding event: {event}")
            yield event

        time.sleep(poll_interval)
