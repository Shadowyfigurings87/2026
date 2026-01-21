import threading
from .threads import arduino_reader_thread
from .state import latest_line
from .parser import parse_line

def start_arduino_ministry():
    t = threading.Thread(target=arduino_reader_thread, daemon=True)
    t.start()

def arduino_stream():
    last_seen = None
    while True:
        if latest_line and latest_line != last_seen:
            last_seen = latest_line
            yield parse_line(latest_line)
        time.sleep(0.01)
