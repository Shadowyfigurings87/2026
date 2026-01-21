import threading
import time

ser = None
latest_line = None
serial_lock = threading.Lock()

last_command = None
last_command_ts = None
last_ack = None
last_ack_ts = None
last_heartbeat_ts = None

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
    # your get_arduino_metrics() logic goes here unchanged
    ...
