import serial
import threading
import time
import glob

# Global serial handle
ser = None

# Latest telemetry line from Arduino
latest_line = None

# Thread lock for safe writes
serial_lock = threading.Lock()


# ---------------------------------------------------------
# Auto-discovery of Arduino serial port (robust version)
# ---------------------------------------------------------
def find_working_serial_port(baud=9600, timeout=0.1):
    """
    Scans /dev/ttyACM* first, then /dev/ttyUSB*.
    Accepts ACM ports even if silent (Arduino Mega resets on open).
    Tries multiple reads to allow firmware boot time.
    """
    # Prefer ACM devices (Arduino)
    candidates = sorted(glob.glob("/dev/ttyACM*"))

    # Fallback to USB devices
    if not candidates:
        candidates = sorted(glob.glob("/dev/ttyUSB*"))

    for port in candidates:
        try:
            print(f"[Arduino] Tentatively opening {port}...")
            test = serial.Serial(port, baud, timeout=timeout)

            # Allow Arduino to auto-reset and boot
            time.sleep(2)
            test.reset_input_buffer()

            # Try reading multiple lines
            valid = False
            for _ in range(10):
                line = test.readline().decode("utf-8", errors="ignore").strip()
                if line:
                    print(f"[Arduino] Valid ASCII detected on {port}: {line}")
                    valid = True
                    break
                time.sleep(0.1)

            # If no ASCII but it's ACM, accept anyway
            if not valid and port.startswith("/dev/ttyACM"):
                print(f"[Arduino] Accepting ACM port without ASCII: {port}")
                test.close()
                return port

            if valid:
                print(f"[Arduino] Valid port discovered: {port}")
                test.close()
                return port

            test.close()

        except Exception as e:
            print(f"[Arduino] Port {port} failed: {e}")
            continue

    print("[Arduino] ERROR: No valid Arduino serial port found.")
    return None


# ---------------------------------------------------------
# Start Arduino reader thread
# ---------------------------------------------------------
def start_arduino_threads(port=None, baud=9600):
    """
    Opens the serial port and starts the reader thread.
    Writer is handled via write_to_arduino().
    """
    global ser

    # Auto-detect port if not provided
    if port is None:
        port = find_working_serial_port(baud=baud)
        if port is None:
            raise RuntimeError("No working serial port found for Arduino")

    print(f"[Arduino] Opening serial port: {port}")

    ser = serial.Serial(port, baud, timeout=0.1)

    # REQUIRED: allow Arduino to reboot after opening the port
    time.sleep(2)
    ser.reset_input_buffer()

    print("[Arduino] Serial port opened, Arduino should now be running.")

    # Start reader thread
    t = threading.Thread(target=_arduino_reader_thread, daemon=True)
    t.start()

    print("[Arduino] Reader thread started.")


# ---------------------------------------------------------
# Reader thread: continuously update latest_line
# ---------------------------------------------------------
def _arduino_reader_thread():
    global latest_line, ser

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
