# Rover1/ministries/network/packet_builder.py
#
# JSONL packet builders for uplink:
# - handshake (system)
# - heartbeat (system)
# - telemetry (merged ministries)
# - camera (picamera2)

import base64
import time
from datetime import datetime
from ministries.utils.jsonl import encode_jsonl


def now_iso():
    return datetime.utcnow().isoformat() + "Z"


def handshake_packet():
    return encode_jsonl({
        "ministry": "system",
        "event": "handshake",
        "ts": time.time(),
        "timestamp": now_iso(),
    })


def heartbeat_packet():
    return encode_jsonl({
        "ministry": "system",
        "event": "heartbeat",
        "ts": time.time(),
        "timestamp": now_iso(),
    })


def telemetry_packet(obj):
    """
    obj is already a dict from merged_stream().
    We only ensure timestamp formatting.
    """
    obj["timestamp"] = now_iso()
    return encode_jsonl(obj)


def camera_packet(frame_obj):
    """
    frame_obj = {
        "ministry": "picamera2",
        "format": "jpeg",
        "ts": <float>,
        "data": <bytes>
    }
    """
    b64 = base64.b64encode(frame_obj["data"]).decode("ascii")

    packet = {
        "ministry": "picamera2",
        "format": "jpeg",
        "encoding": "base64",
        "ts": frame_obj["ts"],
        "timestamp": now_iso(),
        "data": b64,
    }

    return encode_jsonl(packet)