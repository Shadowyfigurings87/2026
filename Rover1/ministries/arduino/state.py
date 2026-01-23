# ministries/arduino/state.py

import threading
import time

arduino_ready = False

def set_arduino_ready():
    global arduino_ready
    arduino_ready = True

# ---------------------------------------------------------
# Serial handle + lock
# ---------------------------------------------------------
ser = None
serial_lock = threading.Lock()

def set_serial_handle(handle):
    global ser
    with serial_lock:
        ser = handle


# ---------------------------------------------------------
# Latest raw line from Arduino
# ---------------------------------------------------------
latest_line = None

def set_latest_line(line):
    global latest_line
    latest_line = line


# ---------------------------------------------------------
# Command + ACK tracking (required by parser.py)
# ---------------------------------------------------------
_last_command = None
_last_command_ts = None
_last_ack = None
_last_ack_ts = None

def last_command():
    return _last_command

def set_last_command(cmd):
    global _last_command, _last_command_ts
    _last_command = cmd
    _last_command_ts = time.time()

def last_command_ts():
    return _last_command_ts

def last_ack():
    return _last_ack

def set_last_ack(ack):
    global _last_ack, _last_ack_ts
    _last_ack = ack
    _last_ack_ts = time.time()

def last_ack_ts():
    return _last_ack_ts


# ---------------------------------------------------------
# Heartbeat tracking
# ---------------------------------------------------------
_last_heartbeat_ts = None

def last_heartbeat_ts():
    return _last_heartbeat_ts

def set_last_heartbeat_ts(ts):
    global _last_heartbeat_ts
    _last_heartbeat_ts = ts


# ---------------------------------------------------------
# Metrics
# ---------------------------------------------------------
metrics = {
    "bytes_read": 0,
    "lines_read": 0,
    "error_count": 0,
    "reconnect_count": 0,
    "last_error": None,
    "last_reconnect_reason": None,
    "start_ts": time.time(),
}

def get_metrics():
    return metrics
