import socket
import time
from ministries.utils.jsonl import encode_jsonl

def send_jsonl_stream(generator, host, port, reconnect_delay=3):
    while True:
        try:
            print(f"[RedRover] Connecting to {host}:{port}")
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

            # Keepalive so Rover1 knows if RedRover dies
            s.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)

            s.connect((host, port))
            print("[RedRover] Connected.")

            with s:
                for obj in generator():
                    line = encode_jsonl(obj)
                    s.sendall(line.encode("utf-8"))
        except Exception as e:
            print(f"[RedRover] Link error: {e}, retrying in {reconnect_delay}s")
            time.sleep(reconnect_delay)

