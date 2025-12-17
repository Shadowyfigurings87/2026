# ingest/ingest_stdin.py

import sys
import os
import json
import threading
from queue import Queue


def start_stdin_ingest(ingest_queue: Queue):
    """
    Start a background thread that reads JSONL from stdin
    and pushes each frame into the ingest queue.
    """

    def run():
        print("[STDIN] Ingest thread started, reading JSONL from stdin...")

        fd = sys.stdin.fileno()
        buffer = b""

        while True:
            chunk = os.read(fd, 4096)
            if not chunk:
                break

            buffer += chunk

            while b"\n" in buffer:
                line, buffer = buffer.split(b"\n", 1)
                line = line.strip()
                if not line:
                    continue

                try:
                    frame = json.loads(line.decode())
                    ingest_queue.put(frame)
                except Exception as e:
                    print(f"[STDIN] JSON parse error: {e}")

        print("[STDIN] End of stdin stream")

    t = threading.Thread(target=run, daemon=True)
    t.start()
