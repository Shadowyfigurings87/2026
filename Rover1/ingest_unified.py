import json
import time
from collections import deque
from datetime import datetime

from redrover_link.tcp_server import redrover_queue
from arduino import arduino_stream
from ministries.camera.camera import camera_stream
from ministries.health.heartbeat import heartbeat_stream
from ministries.health.watchdog import watchdog_stream


# ---------------------------------------------------------
# RedRover stream (queue consumer)
# ---------------------------------------------------------
def redrover_stream():
    """Yield JSON objects from the RedRover queue."""
    while True:
        line = redrover_queue.get()  # blocks until data arrives
        try:
            obj = json.loads(line)
            yield obj
        except Exception:
            continue


# ---------------------------------------------------------
# Ministry tag injection
# ---------------------------------------------------------
def ensure_ministry(obj, default_ministry):
    """Ensure every object has a 'ministry' tag."""
    if "ministry" not in obj or obj["ministry"] is None:
        obj["ministry"] = default_ministry
    return obj


# ---------------------------------------------------------
# Jitter smoothing (timestamp smoothing)
# ---------------------------------------------------------
class JitterSmoother:
    """
    Simple jitter smoother for timestamps.
    Keeps a small window of recent deltas and smooths spikes.
    """

    def __init__(self, window_size=10, max_spike_factor=3.0):
        self.window = deque(maxlen=window_size)
        self.last_ts = None
        self.max_spike_factor = max_spike_factor

    def smooth(self, ts):
        if self.last_ts is None:
            self.last_ts = ts
            return ts

        delta = ts - self.last_ts
        if delta <= 0:
            ts = self.last_ts + 0.001
            self.last_ts = ts
            return ts

        if self.window:
            avg_delta = sum(self.window) / len(self.window)
            if delta > avg_delta * self.max_spike_factor:
                delta = avg_delta
                ts = self.last_ts + delta

        self.window.append(delta)
        self.last_ts = ts
        return ts


# ---------------------------------------------------------
# Local health logger (Rover1-side)
# ---------------------------------------------------------
def log_health(event_type, data):
    """
    Lightweight local health logger.
    Writes JSONL to rover1_health.log in the project root.
    """
    try:
        entry = {
            "ts": time.time(),
            "kind": "health",
            "event": event_type,
            "data": data,
        }
        line = json.dumps(entry, separators=(",", ":")) + "\n"
        with open("rover1_health.log", "a") as f:
            f.write(line)
    except Exception:
        pass


# ---------------------------------------------------------
# Unified merged stream
# ---------------------------------------------------------
def merged_stream():
    """
    Merge multiple telemetry sources into one unified stream with:
      - Ministry tag injection
      - Priority scheduling (weights)
      - Queue pressure monitoring
      - Jitter smoothing on timestamps
      - Local health logging
      - ISO8601 timestamp injection (required by host DB)
    """

    # Startup packet
    yield {
        "ministry": "system",
        "event": "startup",
        "ts": time.time(),
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }

    arduino_gen = arduino_stream()
    redrover_gen = redrover_stream()
    cam_gen = camera_stream(fps=5)
    hb_gen = heartbeat_stream(interval=5)
    wd_gen = watchdog_stream(check_interval=3)

    smoothers = {
        "arduino": JitterSmoother(),
        "redrover": JitterSmoother(),
        "picamera2": JitterSmoother(),
        "heartbeat": JitterSmoother(),
        "watchdog": JitterSmoother(),
    }

    weights = {
        "arduino": 3,
        "redrover": 2,
        "picamera2": 1,
        "heartbeat": 1,
        "watchdog": 1,
    }

    high_pressure_threshold = 500
    critical_pressure_threshold = 1000
    last_pressure_log = 0
    pressure_log_interval = 5  # seconds

    while True:

        # -----------------------------
        # 1. Arduino
        # -----------------------------
        for _ in range(weights["arduino"]):
            try:
                obj = next(arduino_gen)
                obj = ensure_ministry(obj, "arduino")

                ts = obj.get("ts", time.time())
                obj["ts"] = smoothers["arduino"].smooth(ts)

                obj["timestamp"] = datetime.utcnow().isoformat() + "Z"
                yield obj
            except Exception:
                break

        # -----------------------------
        # 2. RedRover
        # -----------------------------
        for _ in range(weights["redrover"]):
            try:
                obj = next(redrover_gen)
                obj = ensure_ministry(obj, "redrover")

                ts = obj.get("ts", time.time())
                obj["ts"] = smoothers["redrover"].smooth(ts)

                # Queue pressure
                try:
                    qsize = redrover_queue.qsize()
                    obj["_queue_pressure"] = qsize
                except Exception:
                    obj["_queue_pressure"] = None

                now = time.time()
                if obj.get("_queue_pressure") is not None and now - last_pressure_log > pressure_log_interval:
                    if qsize > critical_pressure_threshold:
                        log_health("redrover_queue_critical", {"qsize": qsize})
                    elif qsize > high_pressure_threshold:
                        log_health("redrover_queue_high", {"qsize": qsize})
                    last_pressure_log = now

                obj["timestamp"] = datetime.utcnow().isoformat() + "Z"
                yield obj
            except Exception:
                break

        # -----------------------------
        # 3. Camera (picamera2)
        # -----------------------------
        for _ in range(weights["picamera2"]):
            try:
                obj = next(cam_gen)
                obj = ensure_ministry(obj, "picamera2")

                ts = obj.get("ts", time.time())
                obj["ts"] = smoothers["picamera2"].smooth(ts)

                obj["timestamp"] = datetime.utcnow().isoformat() + "Z"
                yield obj
            except Exception:
                break

        # -----------------------------
        # 4. Heartbeat
        # -----------------------------
        for _ in range(weights["heartbeat"]):
            try:
                obj = next(hb_gen)
                obj = ensure_ministry(obj, "heartbeat")

                ts = obj.get("ts", time.time())
                obj["ts"] = smoothers["heartbeat"].smooth(ts)

                obj["timestamp"] = datetime.utcnow().isoformat() + "Z"
                yield obj
            except Exception:
                break

        # -----------------------------
        # 5. Watchdog
        # -----------------------------
        for _ in range(weights["watchdog"]):
            try:
                obj = next(wd_gen)
                obj = ensure_ministry(obj, "watchdog")

                ts = obj.get("ts", time.time())
                obj["ts"] = smoothers["watchdog"].smooth(ts)

                obj["timestamp"] = datetime.utcnow().isoformat() + "Z"
                yield obj
            except Exception:
                break

        time.sleep(0.001)
