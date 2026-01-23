# ministries/arduino/discovery.py

import glob
import time
import os
import serial

BAUD_RATE = 9600


def find_working_serial_port(baud: int = BAUD_RATE, timeout: float = 0.1):
    """
    Sovereign-grade Arduino port discovery:

      1. Prefer stable /dev/serial/by-id paths (best, deterministic).
      2. Resolve symlinks to reveal the actual ACM/USB device.
      3. Fall back to enumerating /dev/ttyACM* and /dev/ttyUSB*.
      4. Validate ASCII output when possible.
      5. Accept silent ACM ports (Mega resets on open).
      6. Log every decision for cockpit visibility.

    Returns:
        str | None
    """

    # ---------------------------------------------------------
    # 1. Stable by-id symlinks (BEST)
    # ---------------------------------------------------------
    by_id = sorted(glob.glob("/dev/serial/by-id/*Arduino*"))
    if by_id:
        symlink = by_id[0]
        resolved = os.path.realpath(symlink)
        print(f"[Arduino] Using stable by-id path: {symlink} -> {resolved}")
        return resolved

    # ---------------------------------------------------------
    # 2. Fallback: ACM/USB enumeration
    # ---------------------------------------------------------
    candidates = sorted(glob.glob("/dev/ttyACM*")) or sorted(glob.glob("/dev/ttyUSB*"))

    if not candidates:
        print("[Arduino] No ACM/USB serial devices detected.")
        return None

    print(f"[Arduino] Scanning candidates: {candidates}")

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
                print(f"[Arduino] Accepting silent ACM port: {port}")
                test.close()
                return port

            test.close()

        except Exception as e:
            print(f"[Arduino] Port {port} failed: {e}")

    print("[Arduino] ERROR: No valid Arduino serial port found.")
    return None
