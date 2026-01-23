# ministries/arduino/serial_link.py

import time
import serial

from .discovery import find_working_serial_port
from .state import metrics

BAUD_RATE = 9600


def open_serial_port():
    """
    Opens the Arduino serial port using robust autodiscovery.
    This function is called by the Arduino reader thread whenever
    a reconnect is needed.

    Returns:
        serial.Serial instance (open and ready)

    Raises:
        RuntimeError if no valid port is found
    """

    port = find_working_serial_port(baud=BAUD_RATE)
    if port is None:
        metrics["error_count"] += 1
        metrics["last_error"] = "No working serial port found"
        raise RuntimeError("No working serial port found for Arduino")

    try:
        s = serial.Serial(port, BAUD_RATE, timeout=0.1)

        # Allow Arduino to reboot after opening the port
        time.sleep(2)
        s.reset_input_buffer()

        metrics["last_error"] = None
        print(f"[Arduino] Serial port opened: {port}")

        return s

    except Exception as e:
        metrics["error_count"] += 1
        metrics["last_error"] = str(e)
        print(f"[Arduino] ERROR opening serial port {port}: {e}")
        raise
