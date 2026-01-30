# ministries/arduino/parser.py

import time

from Rover1.ministries.arduino.state import (
    set_last_heartbeat_ts,
    set_last_ack,
    last_command_ts,
)


def parse_line(line: str):
    """
    Parse a raw line from Arduino into a structured JSON telemetry event.

    Converts legacy ASCII telemetry (TEL:...) into clean JSON fields:
        rpm, throttle, direction, pwm

    Removes all ASCII 'raw' pollution so the host ingestion pipeline
    will always treat this as JSON telemetry.
    """

    now = time.time()

    # ---------------------------------------------------------
    # Heartbeat
    # ---------------------------------------------------------
    if line.startswith("HB:"):
        set_last_heartbeat_ts(now)
        return {
            "ministry": "arduino",
            "event": "heartbeat",
            "ts": now,
        }

    # ---------------------------------------------------------
    # ACK
    # ---------------------------------------------------------
    if line.startswith("ACK:"):
        parts = line.split(":")

        cmd = parts[1] if len(parts) > 1 else None
        val = parts[2] if len(parts) > 2 else None

        set_last_ack(line)

        cmd_ts = last_command_ts()
        latency = None
        if cmd_ts is not None:
            latency = now - cmd_ts

        return {
            "ministry": "arduino",
            "event": "ack",
            "ts": now,
            "command": cmd,
            "value": val,
            "latency": latency,
        }

    # ---------------------------------------------------------
    # TELEMETRY (ASCII → JSON conversion)
    # ---------------------------------------------------------
    if line.startswith("TEL:"):
        # Example: TEL:RPM:123.4 THR:0.00 DIR:FWD PWM:120
        payload = line[4:].strip()
        fields = payload.split()

        data = {}
        for f in fields:
            if ":" in f:
                k, v = f.split(":", 1)
                k = k.lower().strip()
                v = v.strip()

                # Convert numeric fields
                try:
                    data[k] = float(v)
                except ValueError:
                    data[k] = v

        # Normalize keys
        rpm = data.get("rpm")
        throttle = data.get("thr") or data.get("throttle")
        direction = data.get("dir")
        pwm = data.get("pwm")

        return {
            "ministry": "arduino",
            "event": "telemetry",
            "ts": now,
            "rpm": rpm,
            "throttle": throttle,
            "direction": direction,
            "pwm": pwm,
        }

    # ---------------------------------------------------------
    # Fallback: ignore raw noise
    # ---------------------------------------------------------
    return {
        "ministry": "arduino",
        "event": "raw",
        "ts": now,
        "line": line,
    }
