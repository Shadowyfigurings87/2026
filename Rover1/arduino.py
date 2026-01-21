import serial
import threading
import time
import glob
from typing import Optional, Dict, Generator

# ---------------------------------------------------------
# Global state
# ---------------------------------------------------------

ser: Optional[serial.Serial] = None
latest_line: Optional[str] = None

serial_lock = threading.Lock()

# Command/ACK tracking
last_command: Optional[str] = None
last_command_ts: Optional[float] = None
last_ack: Optional[str] = None
last_ack_ts: Optional[float] = None

# Heartbeat tracking
last_heartbeat_ts: Optional[float] = None

# Health metrics
metrics = {
    "bytes_read": 0,
    "lines_read": 0,
    "error_count": 0,
    "reconnect_count": 0,
    "last_error": None,
    "last_reconnect_reason": None,
    "start_ts": time.time(),
}

# Config
BAUD_RATE = 9600
HEARTBEAT_TIMEOUT = 2.0      # seconds without HB → suspect dead
RECONNECT_BACKOFF = 2.0      # seconds between reconnect attempts


# ---------------------------------------------------------
# Robust Arduino port discovery
# ---------------------------------------------------------
def find_working_serial_port(baud: int = BAUD_RATE, timeout: float = 0.1) -> Optional[str]:
    """
    Robust Arduino port discovery:
    1. Prefer stable /dev/serial/by-id paths.
    2. Fall back to ACM/USB enumeration.
    3. Accept ACM ports even if silent (Mega resets on open).
    """

    # 1. Stable by-id symlinks (BEST)
    by_id = sorted(glob.glob("/dev/serial/by-id/*Arduino*"))
    if by_id:
        print(f"[Arduino] Using stable by-id path: {by_id[0]}")
        return by_id[0]

    # 2. Fallback: ACM/USB enumeration
    candidates = sorted(glob.glob("/dev/ttyACM*")) or sorted(glob.glob("/dev/ttyUSB*"))

    for port in candidates:
        try:
            print(f"[Arduino] Tentatively opening {port}...")
            test = serial.Serial(port, baud, timeout=timeout)

            # Allow Arduino to auto-reset and boot
            time.sleep(2)
            test.reset_input_buffer()

            # Try reading multiple lines
            for _ in range(10):
                raw = test.readline()
                if raw:
                    line = raw.decode("utf-8", errors="ignore").strip()
                    if line:
                        print(f"[Arduino] Valid ASCII detected on {port}: {line}")
                        test.close()
                        return port
                time.sleep(0.1)

            # Accept ACM ports even if silent
            if port.startswith("/dev/ttyACM"):
                print(f"[Arduino] Accepting ACM port without ASCII: {port}")
                test.close()
                return port

            test.close()

        except Exception as e:
            print(f"[Arduino] Port {port} failed: {e}")

    print("[Arduino] ERROR: No valid Arduino serial port found.")
    return None


# ---------------------------------------------------------
# Open port (with autodiscovery) and return serial handle
# ---------------------------------------------------------
def _open_serial_port() -> serial.Serial:
    port = find_working_serial_port(baud=BAUD_RATE)
    if port is None:
        raise RuntimeError("No working serial port found for Arduino")

    print(f"[Arduino] Opening serial port: {port}")
    s = serial.Serial(port, BAUD_RATE, timeout=0.1)

    # Allow Arduino to reboot after opening the port
    time.sleep(2)
    s.reset_input_buffer()

    print("[Arduino] Serial port opened, Arduino should now be running.")
    return s


# ---------------------------------------------------------
# Start Arduino reader thread (with reconnect logic)
# ---------------------------------------------------------
def start_arduino_threads():
    """
    Opens the serial port and starts the reader thread.
    Writer is handled via write_to_arduino().
    """
    global ser

    if ser is None:
        ser = _open_serial_port()

    t = threading.Thread(target=_arduino_reader_thread, daemon=True)
    t.start()

    print("[Arduino] Reader thread started.")


# ---------------------------------------------------------
# Internal: parse a single line into structured event(s)
# ---------------------------------------------------------
def _parse_line(line: str) -> Dict:
    """
    Parse a raw line from Arduino into a structured event dict.
    This is intentionally simple and can be extended as needed.

    Expected patterns (examples):
        HB:123456
        ACK:PWM:200
        TEL:RPM:123.4 V:11.8 I:0.42
    """
    global last_heartbeat_ts, last_ack, last_ack_ts

    now = time.time()

    # Heartbeat
    if line.startswith("HB:"):
        last_heartbeat_ts = now
        return {
            "ministry": "arduino",
            "event": "heartbeat",
            "ts": now,
            "raw": line,
        }

    # ACK
    if line.startswith("ACK:"):
        last_ack = line
        last_ack_ts = now

        # Try to extract command + value
        parts = line.split(":")
        cmd = parts[1] if len(parts) > 1 else None
        val = parts[2] if len(parts) > 2 else None

        latency = None
        if last_command_ts is not None:
            latency = now - last_command_ts

        return {
            "ministry": "arduino",
            "event": "ack",
            "ts": now,
            "raw": line,
            "command": cmd,
            "value": val,
            "latency": latency,
        }

    # Telemetry (generic)
    if line.startswith("TEL:"):
        # Example: TEL:RPM:123.4 V:11.8 I:0.42
        payload = line[4:].strip()
        fields = payload.split()
        data = {}
        for f in fields:
            if ":" in f:
                k, v = f.split(":", 1)
                try:
                    data[k.lower()] = float(v)
                except ValueError:
                    data[k.lower()] = v

        return {
            "ministry": "arduino",
            "event": "telemetry",
            "ts": now,
            "raw": line,
            "data": data,
        }

    # Fallback: raw line
    return {
        "ministry": "arduino",
        "event": "raw",
        "ts": now,
        "raw": line,
    }


# ---------------------------------------------------------
# Reader thread: reconnect, heartbeat, metrics
# ---------------------------------------------------------
def _arduino_reader_thread():
    global ser, latest_line, metrics

    while True:
        if ser is None or not ser.is_open:
            # Attempt reconnect
            try:
                print("[Arduino] Serial not open, attempting reconnect...")
                metrics["reconnect_count"] += 1
                metrics["last_reconnect_reason"] = "port_closed"
                ser = _open_serial_port()
            except Exception as e:
                metrics["error_count"] += 1
                metrics["last_error"] = str(e)
                print(f"[Arduino] Reconnect failed: {e}")
                time.sleep(RECONNECT_BACKOFF)
                continue

        try:
            raw = ser.readline()

            if not raw:
                # Heartbeat timeout check
                _check_heartbeat()
                time.sleep(0.01)
                continue

            metrics["bytes_read"] += len(raw)

            line = raw.decode("utf-8", errors="ignore").strip()
            if line:
                metrics["lines_read"] += 1
                latest_line = line

        except Exception as e:
            metrics["error_count"] += 1
            metrics["last_error"] = str(e)
            metrics["last_reconnect_reason"] = "serial_exception"
            print(f"[Arduino] Reader error: {e}")

            # Close and force reconnect
            try:
                if ser and ser.is_open:
                    ser.close()
            except Exception:
                pass

            ser = None
            time.sleep(RECONNECT_BACKOFF)


def _check_heartbeat():
    """
    Check if heartbeat is overdue and, if so, mark ministry as degraded
    and optionally trigger reconnect logic (here we just emit metrics).
    """
    global last_heartbeat_ts, metrics

    now = time.time()
    if last_heartbeat_ts is None:
        return

    age = now - last_heartbeat_ts
    if age > HEARTBEAT_TIMEOUT:
        # We don't force reconnect here, but we mark it in metrics.
        metrics["last_reconnect_reason"] = f"heartbeat_timeout_{age:.2f}s"


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
    global ser, last_command, last_command_ts

    if ser is None or not ser.is_open:
        print("[Arduino] ERROR: Serial port not initialized or not open.")
        return

    try:
        with serial_lock:
            ser.write((msg + "\n").encode("utf-8"))
        last_command = msg
        last_command_ts = time.time()
    except Exception as e:
        metrics["error_count"] += 1
        metrics["last_error"] = str(e)
        print(f"[Arduino] Write error: {e}")


# ---------------------------------------------------------
# Generator: yields structured Arduino events
# ---------------------------------------------------------
def arduino_stream() -> Generator[Dict, None, None]:
    """
    Yields structured event dicts from Arduino firmware.
    Example output:
        { "ministry": "arduino", "event": "telemetry", ... }
        { "ministry": "arduino", "event": "ack", ... }
        { "ministry": "arduino", "event": "heartbeat", ... }
    """
    global latest_line

    last_seen = None

    while True:
        if latest_line and latest_line != last_seen:
            last_seen = latest_line
            yield _parse_line(latest_line)

        time.sleep(0.01)


# ---------------------------------------------------------
# Health metrics accessor
# ---------------------------------------------------------
def get_arduino_metrics() -> Dict:
    """
    Returns a snapshot of Arduino ministry health metrics.
    """
    now = time.time()
    uptime = now - metrics["start_ts"]

    hb_age = None
    if last_heartbeat_ts is not None:
        hb_age = now - last_heartbeat_ts

    ack_latency = None
    if last_ack_ts is not None and last_command_ts is not None:
        ack_latency = last_ack_ts - last_command_ts

    return {
        "ministry": "arduino",
        "uptime": uptime,
        "bytes_read": metrics["bytes_read"],
        "lines_read": metrics["lines_read"],
        "error_count": metrics["error_count"],
        "reconnect_count": metrics["reconnect_count"],
        "last_error": metrics["last_error"],
        "last_reconnect_reason": metrics["last_reconnect_reason"],
        "heartbeat_age": hb_age,
        "last_command": last_command,
        "last_ack": last_ack,
        "last_ack_latency": ack_latency,
    }
