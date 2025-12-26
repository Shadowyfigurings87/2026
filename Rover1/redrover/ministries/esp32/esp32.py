import time
import json
import serial
import serial.tools.list_ports
from ministries.utils.jsonl import now_ts


def find_esp32_port():
    """
    Scan available serial ports and return the first one that looks like an ESP32.
    This allows RedRover to run even if the ESP32 is not plugged in yet.
    """
    for port in serial.tools.list_ports.comports():
        name = port.device.lower()
        desc = port.description.lower()
        if "usb" in name or "uart" in desc or "cp210" in desc or "ch910" in desc:
            return port.device
    return None


def esp32_stream(baud=115200):
    """
    Robust ESP32 telemetry stream.
    Reads JSON lines from the ESP32 and yields them as RedRover packets.

    If the ESP32 is not connected, yields a heartbeat error every few seconds.
    """

    ser = None
    last_attempt = 0

    while True:
        try:
            # If not connected, try to find a port every 3 seconds
            if ser is None or not ser.is_open:
                now = time.time()
                if now - last_attempt > 3:
                    last_attempt = now
                    port = find_esp32_port()
                    if port:
                        try:
                            ser = serial.Serial(port, baud, timeout=0.1)
                        except Exception:
                            ser = None

                if ser is None:
                    yield {
                        "kind": "telemetry",
                        "source": "esp32",
                        "rover": "RedRover",
                        "ts": now_ts(),
                        "error": "esp32_not_connected"
                    }
                    time.sleep(1)
                    continue

            # Try reading a line
            line = ser.readline().decode("utf-8", errors="ignore").strip()

            if not line:
                # No data — yield a heartbeat packet
                yield {
                    "kind": "telemetry",
                    "source": "esp32",
                    "rover": "RedRover",
                    "ts": now_ts(),
                    "data": {"status": "idle"}
                }
                continue

            # Try parsing JSON from ESP32
            try:
                obj = json.loads(line)
                yield {
                    "kind": "telemetry",
                    "source": "esp32",
                    "rover": "RedRover",
                    "ts": now_ts(),
                    "data": obj
                }
            except json.JSONDecodeError:
                yield {
                    "kind": "telemetry",
                    "source": "esp32",
                    "rover": "RedRover",
                    "ts": now_ts(),
                    "error": "bad_json",
                    "raw": line
                }

        except Exception as e:
            yield {
                "kind": "telemetry",
                "source": "esp32",
                "rover": "RedRover",
                "ts": now_ts(),
                "error": str(e)
            }
            time.sleep(1)
            ser = None

