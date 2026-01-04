import serial
import threading
import time

# Global serial handle
ser = None

# Latest telemetry line from Arduino
latest_line = None

# Thread lock for safe writes
serial_lock = threading.Lock()


# ---------------------------------------------------------
# Start Arduino reader thread
# ---------------------------------------------------------
def start_arduino_threads(port="/dev/ttyACM0", baud=115200):
    """
    Opens the serial port and starts the reader thread.
    Writer is handled via write_to_arduino().
    """
    global ser
    ser = serial.Serial(port, baud, timeout=0.1)

    t = threading.Thread(target=_arduino_reader_thread, daemon=True)
    t.start()

    print("[Arduino] Reader thread started.")


# ---------------------------------------------------------
# Reader thread: continuously update latest_line
# ---------------------------------------------------------
def _arduino_reader_thread():
    global latest_line

    while True:
        try:
            line = ser.readline().decode("utf-8", errors="ignore").strip()
            if line:
                latest_line = line
        except Exception:
            pass

        time.sleep(0.001)


# ---------------------------------------------------------
# Thread‑safe writer for motor.py and other ministries
# ---------------------------------------------------------
def write_to_arduino(msg: str):
    """
    Sends a command string to the Arduino.
    Example:
        write_to_arduino("ACT:FWD:120")
        write_to_arduino("PWM:200")
        write_to_arduino("DIR:REV")
    """
    global ser

    if ser is None:
        print("[Arduino] ERROR: Serial port not initialized.")
        return

    try:
        with serial_lock:
            ser.write((msg + "\n").encode("utf-8"))
    except Exception as e:
        print(f"[Arduino] Write error: {e}")


# ---------------------------------------------------------
# Generator: yields Arduino telemetry as dicts
# ---------------------------------------------------------
def arduino_stream():
    """
    Yields telemetry dicts from Arduino firmware.
    Example output:
        { "ministry": "arduino", "ts": 123456.78, "raw": "RPM:1234" }
        { "ministry": "arduino", "ts": 123456.79, "raw": "ACK:PWM:200" }
    """
    global latest_line

    while True:
        if latest_line:
            yield {
                "ministry": "arduino",
                "ts": time.time(),
                "raw": latest_line
            }

        time.sleep(0.01)
