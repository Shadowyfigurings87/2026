# ministries/arduino/state.py

import threading
import time

# ---------------------------------------------------------
# Global state
# ---------------------------------------------------------

_ser = None
_latest_line = None
_serial_lock = threading.Lock()

_last_command = None
_last_command_ts = None
_last_ack = None
_last_ack_ts = None
_last_heartbeat_ts = None

_metrics = {
    "bytes_read": 0,
    "lines_read": 0,
    "error_count": 0,
    "reconnect_count": 0,
    "last_error": None,
    "last_reconnect_reason": None,
    "start_ts": time.time(),
}


# ---------------------------------------------------------
# Serial handle management
# ---------------------------------------------------------

def ser():
    return _ser

def set_serial_handle(handle):
    global _ser
    _ser = handle


def serial_lock():
    return _serial_lock


# ---------------------------------------------------------
# Latest line (raw Arduino telemetry)
# ---------------------------------------------------------

def latest_line():
    return _latest_line

def set_latest_line(line: str):
    global _latest_line
    _latest_line = line


# ---------------------------------------------------------
# Command / ACK tracking
# ---------------------------------------------------------

def last_command():
    return _last_command

def last_command_ts():
    return _last_command_ts

def set_last_command(cmd: str):
    global _last_command, _last_command_ts
    _last_command = cmd
    _last_command_ts = time.time()


def last_ack():
    return _last_ack

def last_ack_ts():
    return _last_ack_ts

def set_last_ack(ack: str):
    global _last_ack, _last_ack_ts
    _last_ack = ack
    _last_ack_ts = time.time()


# ---------------------------------------------------------
# Heartbeat tracking
# ---------------------------------------------------------

def last_heartbeat_ts():
    return _last_heartbeat_ts

def set_last_heartbeat_ts(ts: float):
    global _last_heartbeat_ts
    _last_heartbeat_ts = ts


# ---------------------------------------------------------
# Metrics
# ---------------------------------------------------------

def metrics():
    return _metrics


def get_metrics():
    """
    Returns a snapshot of Arduino ministry health metrics.
    Mirrors the old get_arduino_metrics() behavior.
    """

    now = time.time()
    uptime = now - _metrics["start_ts"]

    hb_age = None
    if _last_heartbeat_ts is not None:
        hb_age = now - _last_heartbeat_ts

    ack_latency = None
    if _last_ack_ts is not None and _last_command_ts is not None:
        ack_latency = _last_ack_ts - _last_command_ts

    return {
        "ministry": "arduino",
        "uptime": uptime,
        "bytes_read": _metrics["bytes_read"],
        "lines_read": _metrics["lines_read"],
        "error_count": _metrics["error_count"],
        "reconnect_count": _metrics["reconnect_count"],
        "last_error": _metrics["last_error"],
        "last_reconnect_reason": _metrics["last_reconnect_reason"],
        "heartbeat_age": hb_age,
        "last_command": _last_command,
        "last_ack": _last_ack,
        "last_ack_latency": ack_latency,
    }
