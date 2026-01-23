# ministries/arduino/threads.py

import time
import serial

from .state import (
    ser,
    set_serial_handle,
    latest_line,
    set_latest_line,
    metrics,
    last_heartbeat_ts,
    set_last_heartbeat_ts,
)
from .serial_link import open_serial_port
from .parser import parse_line


HEARTBEAT_TIMEOUT = 2.0        # seconds without HB → suspect dead
RECONNECT_BACKOFF = 2.0        # seconds between reconnect attempts


def arduino_reader_thread():
    """
    Robust Arduino reader thread:
      - Opens serial port (with autodiscovery)
      - Reads raw lines
      - Parses them
      - Updates latest_line for arduino_stream()
      - Tracks metrics
      - Handles reconnects
      - Handles heartbeat timeout
    """

    global ser

    while True:
        # ---------------------------------------------------------
        # Ensure serial port is open
        # ---------------------------------------------------------
        if ser is None or not ser.is_open:
            try:
                print("[Arduino] Serial not open, attempting reconnect…")
                metrics["reconnect_count"] += 1
                metrics["last_reconnect_reason"] = "port_closed"

                new_ser = open_serial_port()
                set_serial_handle(new_ser)
                print("[Arduino] Serial port opened successfully")

            except Exception as e:
                metrics["error_count"] += 1
                metrics["last_error"] = str(e)
                print(f"[Arduino] Reconnect failed: {e}")
                time.sleep(RECONNECT_BACKOFF)
                continue

        # ---------------------------------------------------------
        # Read a line
        # ---------------------------------------------------------
        try:
            raw = ser.readline()

            if not raw:
                _check_heartbeat()
                time.sleep(0.01)
                continue

            metrics["bytes_read"] += len(raw)

            line = raw.decode("utf-8", errors="ignore").strip()
            if not line:
                continue

            metrics["lines_read"] += 1

            # -----------------------------------------------------
            # Parse the line into a structured event
            # -----------------------------------------------------
            event = parse_line(line)

            # Heartbeat tracking
            if isinstance(event, dict) and event.get("event") == "heartbeat":
                set_last_heartbeat_ts(time.time())

            # -----------------------------------------------------
            # Update latest_line for arduino_stream()
            # -----------------------------------------------------
            set_latest_line(line)

        except Exception as e:
            metrics["error_count"] += 1
            metrics["last_error"] = str(e)
            metrics["last_reconnect_reason"] = "serial_exception"
            print(f"[Arduino] Reader error: {e}")

            # Force reconnect
            try:
                if ser and ser.is_open:
                    ser.close()
            except Exception:
                pass

            set_serial_handle(None)
            time.sleep(RECONNECT_BACKOFF)


def _check_heartbeat():
    """
    Check if heartbeat is overdue and mark ministry as degraded.
    """
    ts = last_heartbeat_ts()
    if ts is None:
        return

    age = time.time() - ts
    if age > HEARTBEAT_TIMEOUT:
        metrics["last_reconnect_reason"] = f"heartbeat_timeout_{age:.2f}s"
