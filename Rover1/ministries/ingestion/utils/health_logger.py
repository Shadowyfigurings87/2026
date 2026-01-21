# ingestion/utils/health_logger.py

import json
import time

def log_health(event_type, data):
    try:
        entry = {
            "ts": time.time(),
            "kind": "health",
            "event": event_type,
            "data": data,
        }
        with open("rover1_health.log", "a") as f:
            f.write(json.dumps(entry) + "\n")
    except Exception:
        pass
