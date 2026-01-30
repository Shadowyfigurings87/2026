# Rover1/ministries/arduino/commands.py

import time

from Rover1.ministries.arduino.state import (
    ser,                    # now a function returning the serial handle
    serial_lock,            # a Lock object, NOT callable
    set_last_command,
    get_metrics,            # use accessor for metrics dict
)
from Rover1.ministries.arduino.serial_link import open_serial_port


def _ensure_serial():
    """
    Ensures the Arduino serial port is open.
    The reader thread normally owns reconnect logic, but commands
    may be sent before the reader thread has completed initialization.
    """

    handle = ser()  # correct: ser() returns the current serial handle

    if handle is None or not handle.is_open:
        try:
            new_handle = open_serial_port()
            print("[Arduino/Commands] Serial port opened for command uplink")
            return new_handle
        except Exception as e:
            m = get_metrics()
            m["error_count"] += 1
            m["last_error"] = f"uplink_open_failed: {e}"
            print(f"[Arduino/Commands] ERROR opening serial port: {e}")
            return None

    return handle


def send_arduino_command(msg: str):
    """
    Unified command uplink for all ministries.

    This function:
      - ensures the serial port is open
      - writes the command with newline termination
      - updates command tracking (for ACK latency)
      - updates metrics on error
    """

    handle = _ensure_serial()
    if handle is None or not handle.is_open:
        print("[Arduino/Commands] ERROR: Serial port not initialized or not open.")
        m = get_metrics()
        m["error_count"] += 1
        m["last_error"] = "uplink_no_serial"
        return

    try:
        # serial_lock is a Lock object, so we use it directly
        with serial_lock:
            handle.write((msg + "\n").encode("utf-8"))
            handle.flush()

        # Track command + timestamp for ACK latency
        set_last_command(msg)

        m = get_metrics()
        m["commands_sent"] = m.get("commands_sent", 0) + 1
        m["last_command"] = msg

        print(f"[Arduino/Commands] → {msg}")

    except Exception as e:
        m = get_metrics()
        m["error_count"] += 1
        m["last_error"] = str(e)
        print(f"[Arduino/Commands] Write error: {e}")
