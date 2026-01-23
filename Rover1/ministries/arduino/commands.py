# ministries/arduino/commands.py

import time
from .state import (
    ser,
    serial_lock,
    set_last_command,
    metrics,
)


def write_to_arduino(msg: str):
    """
    Thread‑safe writer for sending commands to the Arduino.

    Example:
        write_to_arduino("ACT:FWD:120")
        write_to_arduino("PWM:200")
        write_to_arduino("DIR:REV")

    This function:
      - ensures the serial port is open
      - writes the command with newline termination
      - updates command tracking (for ACK latency)
      - updates metrics on error
    """

    handle = ser()
    if handle is None or not handle.is_open:
        print("[Arduino] ERROR: Serial port not initialized or not open.")
        metrics()["error_count"] += 1
        metrics()["last_error"] = "write_no_serial"
        return

    try:
        with serial_lock():
            handle.write((msg + "\n").encode("utf-8"))

        # Track command + timestamp for ACK latency
        set_last_command(msg)

    except Exception as e:
        metrics()["error_count"] += 1
        metrics()["last_error"] = str(e)
        print(f"[Arduino] Write error: {e}")
