import socket
import time
from ministries.utils.jsonl import encode_jsonl

def send_jsonl_stream(generator, host="192.168.1.50", port=9100, reconnect_delay=5):
    """
    generator: yields dict objects to send as JSONL
    """
    while True:
        try:
            print(f"[RedRover] Connecting to {host}:{port}")
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((host, port))
            with s:
                for obj in generator():
                    line = encode_jsonl(obj)
                    s.sendall(line.encode("utf-8"))
        except Exception as e:
            print(f"[RedRover] Link error: {e}, reconnecting in {reconnect_delay}s")
            time.sleep(reconnect_delay)
