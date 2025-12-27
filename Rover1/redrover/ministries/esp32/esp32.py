import time
import json
import serial
import serial.tools.list_ports
from ministries.utils.jsonl import encode_jsonl


def find_esp32_port():
    """
    Scan available serial ports and return the first one that looks like an ESP32.
    Allows RedRover to run even if the ESP32 is not plugged in yet.
    """
    for port in serial.tools.list_ports.comports():
        name = port.device.lower()
        desc = port.description.lower()
        if (
            "usb" in name
            or "uart" in desc
            or "cp210" in desc
            or "ch910" in desc
            or "esp" in desc
        ):
            return port.device
    return None


def open_serial(port, baud=115200):
    """Try to open a serial connection safely."""
    try:
        return serial.Serial(port, baud, timeout=0.1)
    except Exception:
        return None


def read_esp32_line(ser):
    """Read one line from ESP32, return None if empty."""
    try:
        line = ser.readline().decode("utf-8", errors="ignore").strip()
        return line if line else None
    except Exception:
        return None


def main():
    ser = None
    last_port_scan = 0

    while True:
        try:
            # If not connected, scan for ESP32 every 3 seconds
            if ser is None or not ser.is_open:
                now = time.time()
                if now - last_port_scan > 3:
                    last_port_scan = now
                    port = find_esp32_port()
                    if port:
                        ser = open_serial(port)

                if ser is None:
                    # ESP32 not connected — emit heartbeat error
                    obj = {
                        "ministry": "esp32",
                        "ts": time.time(),
                        "status": "not_connected"
                    }
                    print(encode_jsonl(obj), end="", flush=True)
                    time.sleep(1)
                    continue

            # Try reading a line from ESP32
            line = read_esp32_line(ser)

            if line is None:
                # No data — emit idle heartbeat
                obj = {
                    "ministry": "esp32",
                    "ts": time.time(),
                    "status": "idle"
                }
                print(encode_jsonl(obj), end="", flush=True)
                continue

            # Try parsing JSON from ESP32
            try:
                data = json.loads(line)
                obj = {
                    "ministry": "esp32",
                    "ts": time.time(),
                    "data": data
                }
            except json.JSONDecodeError:
                obj = {
                    "ministry": "esp32",
                    "ts": time.time(),
                    "error": "bad_json",
                    "raw": line
                }

            print(encode_jsonl(obj), end="", flush=True)

        except Exception as e:
            # Generic error — reset serial and retry
            obj = {
                "ministry": "esp32",
                "ts": time.time(),
                "error": str(e)
            }
            print(encode_jsonl(obj), end="", flush=True)
            time.sleep(1)
            ser = None


if __name__ == "__main__":
    main()
