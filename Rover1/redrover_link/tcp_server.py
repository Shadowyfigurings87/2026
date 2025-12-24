import socket
import threading
import queue

redrover_queue = queue.Queue()  # raw JSONL lines from RedRover

def _handle_client(conn):
    with conn, conn.makefile("r") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            redrover_queue.put(line)

def start_redrover_server(host="0.0.0.0", port=9100):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((host, port))
    s.listen(2)
    print(f"[RedRoverLink] Listening on {host}:{port}")

    def accept_loop():
        while True:
            conn, addr = s.accept()
            print(f"[RedRoverLink] Connection from {addr}")
            t = threading.Thread(target=_handle_client, args=(conn,), daemon=True)
            t.start()

    threading.Thread(target=accept_loop, daemon=True).start()
