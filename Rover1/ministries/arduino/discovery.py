# ministries/arduino/discovery.py

import glob
import time
import serial

BAUD_RATE = 9600


def find_working_serial_port(baud: int = BAUD_RATE, timeout: float = 0.1):
    """
    Robust Arduino port discovery:
      1. Prefer stable /dev/serial/by-id paths.
      2. Fall back to ACM/USB enumeration.
      3. Accept ACM ports even if silent (Mega resets on open).
      4. Validate ASCII output when possible.

    Returns:
        str | None
    """

    # ---------------------------------------------------------
    # 1. Stable by-id symlinks (BEST)
    # ---------------------------------------------------------
    by_id = sorted(glob.glob("/dev/serial/by-id/*Arduino*"))
    if by_id:
        print(f"[Arduino] Using stable by-id path: {by_id[0]}")
        return by_id[0]

    # ---------------------------------------------------------
    # 2. Fallback: ACM/USB enumeration
    # ---------------------------------------------------------
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
