# Rover1/ministries/network/packet_builder.py

import json
import time
from datetime import datetime


def _iso():
    return datetime.utcnow().isoformat() + "Z"


def handshake_packet():
    """
    Initial handshake packet sent once per connection.
    """
    return json.dumps({
        "ministry": "system",
        "event": "handshake",
        "ts": time.time(),
        "timestamp": _iso(),
    }, separators=(",", ":")) + "\n"


def heartbeat_packet():
    """
    Periodic heartbeat packet to keep the uplink alive.
    """
    return json.dumps({
        "ministry": "system",
        "event": "heartbeat",
        "ts": time.time(),
        "timestamp": _iso(),
    }, separators=(",", ":")) + "\n"


def telemetry_packet(obj: dict):
    """
    Build a JSONL telemetry packet.

    Ensures:
      - ministry is present
      - event is present
      - ts is present
      - timestamp is present
    """

    # Ensure required fields
    obj.setdefault("ts", time.time())
    obj.setdefault("timestamp", _iso())
    obj.setdefault("ministry", "unknown")
    obj.setdefault("event", "telemetry")

    return json.dumps(obj, separators=(",", ":")) + "\n"
