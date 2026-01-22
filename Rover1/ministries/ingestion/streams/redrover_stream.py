# ministries/ingestion/streams/redrover_stream.py

import json
from redrover_link.tcp_server import redrover_queue

def redrover_stream():
    while True:
        line = redrover_queue.get()
        try:
            yield json.loads(line)
        except Exception:
            continue
