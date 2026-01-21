import time
import serial
from .discovery import find_working_serial_port
from .state import metrics

BAUD_RATE = 9600

def open_serial_port():
    port = find_working_serial_port(baud=BAUD_RATE)
    if port is None:
        raise RuntimeError("No working serial port found for Arduino")

    s = serial.Serial(port, BAUD_RATE, timeout=0.1)
    time.sleep(2)
    s.reset_input_buffer()
    return s
