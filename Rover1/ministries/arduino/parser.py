# ministries/arduino/parser.py

import time

from .state import (
    set_last_heartbeat_ts,
    set_last_ack,
    last_command_ts,
)


def parse_line(line: str):
    """
    Parse a raw line from Arduino into a structured event dict.

    Supported patterns:
        HB:<value>              → heartbeat
        ACK:<cmd>:<value>       → command acknowledgment
        TEL:<k:v k:v ...>       → telemetry packet
        anything else           → raw event
    """

    now = time.time()

    # ---------------------------------------------------------
    # Heartbeat
    # ---------------------------------------------------------
    if line.startswith("HB:"):
        set_last_heartbeat_ts(now)
        return {
            "event": "heartbeat",
            "raw": line,
            "ts": now,
        }

    # ---------------------------------------------------------
    # ACK
    # ---------------------------------------------------------
    if line.startswith("ACK:"):
        parts = line.split(":")

        cmd = parts[1] if len(parts) > 1 else None
        val = parts[2] if len(parts) > 2 else None

        # Track ACK timestamp
        set_last_ack(line)

        # Compute latency if possible
        cmd_ts = last_command_ts()
        latency = None
        if cmd_ts is not None:
            latency = now - cmd_ts

        return {
            "event": "ack",
            "raw": line,
            "ts": now,
            "command": cmd,
            "value": val,
            "latency": latency,
        }

    # ---------------------------------------------------------
    # Telemetry (generic)
    # ---------------------------------------------------------
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
            "event": "telemetry",
            "raw": line,
            "ts": now,
            "data": data,
        }

    # ---------------------------------------------------------
    # Fallback: raw line
    # ---------------------------------------------------------
    return {
        "event": "raw",
        "raw": line,
        "ts": now,
    }
