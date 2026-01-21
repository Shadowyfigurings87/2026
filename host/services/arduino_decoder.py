# host/services/arduino_decoder.py

def decode_arduino_line(line: str):
    """
    Decodes a single Arduino telemetry line into structured fields.
    Expected format:
      TEL:RPM:<val> THR:<val> DIR:<FWD|REV|STOP> PWM:<0-255>
    """
    if not line:
        return None

    line = line.strip()
    if not line.startswith("TEL:"):
        return None

    parts = line.split()
    out = {}

    for p in parts:
        if p.startswith("TEL:RPM:"):
            try:
                out["rpm"] = float(p.split(":")[2])
            except Exception:
                out["rpm"] = 0.0

        elif p.startswith("THR:"):
            try:
                out["throttle"] = float(p.split(":")[1])
            except Exception:
                out["throttle"] = None

        elif p.startswith("DIR:"):
            out["direction"] = p.split(":")[1]

        elif p.startswith("PWM:"):
            try:
                out["pwm"] = int(p.split(":")[1])
            except Exception:
                out["pwm"] = None

    return out if out else None
