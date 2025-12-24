import json
import queue
import time
from arduino import arduino_telemetry_queue
from redrover_link.tcp_server import redrover_queue
from ministries.utils.jsonl import now_ts

def merged_stream():
    """
    Yields unified telemetry dicts:
    {
      "kind": "telemetry",
      "source": "...",
      "rover": "...",
      "ts": ...,
      "data": { ... }
    }
    """
    while True:
        # Arduino telemetry
        try:
            ar = arduino_telemetry_queue.get_nowait()
            yield {
                "kind": "telemetry",
                "source": "arduino",
                "rover": "Rover1",
                "ts": now_ts(),
                "data": ar,
            }
        except queue.Empty:
            pass

        # RedRover telemetry (already JSON)
        try:
            line = redrover_queue.get_nowait()
            obj = json.loads(line)
            # assume RedRover already sets source/rover/ts, else wrap
            if "kind" not in obj:
                obj["kind"] = "telemetry"
            if "rover" not in obj:
                obj["rover"] = "RedRover"
            if "ts" not in obj:
                obj["ts"] = now_ts()
            yield obj
        except queue.Empty:
            pass
        except json.JSONDecodeError:
            pass

        time.sleep(0.005)
