# Rover1/ministries/network/packet_builder.py

import json
from datetime import datetime


def handshake_packet():
    return json.dumps({
        "ministry": "system",
        "event": "handshake",
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }) + "\n"


def heartbeat_packet():
    return json.dumps({
        "ministry": "system",
        "event": "heartbeat",
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }) + "\n"


def telemetry_packet(obj: dict):
    """
    Build a JSONL telemetry packet.
    """
    return json.dumps(obj, separators=(",", ":")) + "\n"
