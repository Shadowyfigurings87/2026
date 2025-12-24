import threading
import queue
import serial
import json

# Telemetry from Arduino
arduino_telemetry_queue = queue.Queue()
# Commands to Arduino (dicts)
arduino_command_queue = queue.Queue()

def arduino_reader(port="/dev/ttyACM0", baud=115200):
    ser = serial.Serial(port, baud, timeout=1)
    with ser:
        for line in ser:
            line = line.decode("utf-8", errors="ignore").strip()
            if not line:
                continue
            # Assume Arduino prints JSON per line
            try:
                obj = json.loads(line)
                arduino_telemetry_queue.put(obj)
            except json.JSONDecodeError:
                continue

def arduino_writer(port="/dev/ttyACM0", baud=115200):
    ser = serial.Serial(port, baud, timeout=1)
    with ser:
        while True:
            cmd = arduino_command_queue.get()
            line = json.dumps(cmd) + "\n"
            ser.write(line.encode("utf-8"))
            ser.flush()

def start_arduino_threads(port="/dev/ttyACM0", baud=115200):
    t1 = threading.Thread(target=arduino_reader, args=(port, baud), daemon=True)
    t2 = threading.Thread(target=arduino_writer, args=(port, baud), daemon=True)
    t1.start()
    t2.start()
