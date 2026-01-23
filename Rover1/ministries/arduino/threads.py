# ministries/arduino/threads.py

import time
import serial

from ministries.arduino.state import (
    set_latest_line,
    metrics,
    last_heartbeat_ts,
    set_last_heartbeat_ts,
)
from ministries.arduino.serial_link import open_serial_port
from ministries.arduino.parser import parse_line

HEARTBEAT_TIMEOUT = 2.0
RECONNECT_BACKOFF = 2.0


def arduino_reader_thread():
    print("[Arduino] Reader thread starting…")

    ser = None  # local handle owned by this thread

    while True:
        # ---------------------------------------------------------
        # Ensure serial port is open
        # ---------------------------------------------------------
        if ser is None or not ser.is_open:
            try:
                print("[Arduino] Serial not open, attempting reconnect…")
                metrics["reconnect_count"] += 1
                metrics["last_reconnect_reason"] = "port_closed"

                ser = open_serial_port()
                print("[Arduino] Serial port opened successfully")

                # Mark Arduino ministry as ready
                from ministries.arduino.service import mark_arduino_ready
                mark_arduino_ready()

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

            # Parse structured event
            event = parse_line(line)

            # Heartbeat tracking
            if isinstance(event, dict) and event.get("event") == "heartbeat":
                set_last_heartbeat_ts(time.time())

            # Update latest_line for arduino_stream()
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

            ser = None
            time.sleep(RECONNECT_BACKOFF)


def _check_heartbeat():
    ts = last_heartbeat_ts()
    if ts is None:
        return

    age = time.time() - ts
    if age > HEARTBEAT_TIMEOUT:
        metrics["last_reconnect_reason"] = f"heartbeat_timeout_{age:.2f}s"
