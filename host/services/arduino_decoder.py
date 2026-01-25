# host/services/arduino_decoder.py

def decode_arduino_line(line: str):
    """
    Expected format (example):
        TEL rpm=1234 throttle=0.52 direction=FWD pwm=180
    """

    if not line or "TEL" not in line:
        return None

    parts = line.strip().split()
    decoded = {}

    for p in parts:
        if "=" not in p:
            continue

        key, val = p.split("=", 1)

        # Normalize keys
        if key == "rpm":
            decoded["rpm"] = float(val)
        elif key in ("thr", "throttle"):
            decoded["throttle"] = float(val)
        elif key in ("dir", "direction"):
            decoded["direction"] = val
        elif key == "pwm":
            decoded["pwm"] = float(val)

    # Must have at least one valid field
    return decoded if decoded else None
