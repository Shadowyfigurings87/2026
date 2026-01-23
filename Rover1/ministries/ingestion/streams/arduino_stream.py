# ministries/ingestion/streams/arduino_stream.py

import threading
import queue
import time

from ministries.arduino.service import arduino_stream

# Internal queue for Arduino events
_arduino_queue = queue.Queue(maxsize=1000)
_worker_started = False


def _arduino_worker():
    """
    Background worker that consumes the blocking arduino_stream()
    and pushes events into a queue for ingestion to read non-blockingly.
    """
    print("[Ingestion/Arduino] worker thread starting…")
    try:
        gen = arduino_stream()
        for evt in gen:
            try:
                _arduino_queue.put(evt, timeout=1)
            except queue.Full:
                print("[Ingestion/Arduino] queue full, dropping event")
    except Exception as e:
        print(f"[Ingestion/Arduino] worker error: {e}")


def _ensure_worker():
    global _worker_started
    if not _worker_started:
        t = threading.Thread(
            target=_arduino_worker,
            daemon=True,
            name="IngestionArduinoWorker",
        )
        t.start()
        _worker_started = True
        print("[Ingestion/Arduino] worker thread launched")


def arduino_ingest_stream():
    """
    Non-blocking Arduino ingestion generator.

    - Ensures a background worker is running that reads from the
      blocking ministries.arduino.service.arduino_stream().
    - Each next() call tries to pull from the queue with a short timeout.
    - If no data is available, we emit a lightweight 'arduino_idle' event
      so merged_stream never stalls on Arduino.
    """
    _ensure_worker()
    print("[Ingestion/Arduino] arduino_ingest_stream() created")

    while True:
        try:
            evt = _arduino_queue.get(timeout=0.01)
            # Pass through real Arduino events
            yield evt
        except queue.Empty:
            # No new Arduino data right now — emit an idle marker
            yield {
                "event": "arduino_idle",
                "ministry": "arduino",
                "ts": time.time(),
            }
