import time
from .state import ser, latest_line, metrics
from .serial_link import open_serial_port
from .parser import parse_line

def arduino_reader_thread():
    # your _arduino_reader_thread() logic goes here unchanged
    ...

def check_heartbeat():
    # your _check_heartbeat() logic goes here unchanged
    ...
