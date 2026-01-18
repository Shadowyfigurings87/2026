# Rover1/ministries/network/streams.py
#
# Hardened unified stream layer.
# - Telemetry always flows
# - Camera frames interleaved when available
# - If camera fails once, disable permanently
# - No repeated init attempts
# - No unified stream crashes

import time
import json
from collections import deque
from datetime import datetime

from redrover_link.tcp_server import redrover_queue
from arduino import arduino_stream
from ministries.health.heartbeat import heartbeat_stream
from ministries.health.watchdog import watchdog_stream


def now_iso():
    return datetime.utcnow().isoformat() + "Z"


def redrover_stream():
    while True:
        line = redrover_queue.get()
        try:
            yield json.loads(line)
        except Exception:
            continue


def ensure_ministry(obj, default):
    if "ministry" not in obj or obj["ministry"] is None:
        obj["ministry"] = default
    return obj


class JitterSmoother:
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
            avg = sum(self.window) / len(self.window)
            if delta > avg * self.max_spike_factor:
                delta = avg
                ts = self.last_ts + delta

        self.window.append(delta)
        self.last_ts = ts
        return ts


def merged_stream():
    yield {
        "ministry": "system",
        "event": "startup",
        "ts": time.time(),
        "timestamp": now_iso(),
    }

    arduino_gen = arduino_stream()
    redrover_gen = redrover_stream()
    hb_gen = heartbeat_stream(interval=5)
    wd_gen = watchdog_stream(check_interval=3)

    smooth = {
        "arduino": JitterSmoother(),
        "redrover": JitterSmoother(),
        "heartbeat": JitterSmoother(),
        "watchdog": JitterSmoother(),
    }

    weights = {
        "arduino": 3,
        "redrover": 2,
        "heartbeat": 1,
        "watchdog": 1,
    }

    while True:
        # Arduino
        for _ in range(weights["arduino"]):
            try:
                obj = ensure_ministry(next(arduino_gen), "arduino")
                obj["ts"] = smooth["arduino"].smooth(obj.get("ts", time.time()))
                obj["timestamp"] = now_iso()
                yield obj
            except Exception:
                break

        # RedRover
        for _ in range(weights["redrover"]):
            try:
                obj = ensure_ministry(next(redrover_gen), "redrover")
                obj["ts"] = smooth["redrover"].smooth(obj.get("ts", time.time()))
                obj["timestamp"] = now_iso()
                yield obj
            except Exception:
                break

        # Heartbeat
        for _ in range(weights["heartbeat"]):
            try:
                obj = ensure_ministry(next(hb_gen), "heartbeat")
                obj["ts"] = smooth["heartbeat"].smooth(obj.get("ts", time.time()))
                obj["timestamp"] = now_iso()
                yield obj
            except Exception:
                break

        # Watchdog
        for _ in range(weights["watchdog"]):
            try:
                obj = ensure_ministry(next(wd_gen), "watchdog")
                obj["ts"] = smooth["watchdog"].smooth(obj.get("ts", time.time()))
                obj["timestamp"] = now_iso()
                yield obj
            except Exception:
                break

        time.sleep(0.001)


def unified_stream_with_camera(camera_fps=10, camera_weight=5):
    telem_gen = merged_stream()

    # Try to initialize camera generator
    camera_enabled = True
    cam_gen = None

    try:
        from ministries.camera.streamer import camera_frame_generator
        cam_gen = camera_frame_generator(camera_fps=camera_fps)
    except Exception as e:
        print(f"[UnifiedStream] Camera generator init failed: {e}")
        camera_enabled = False

    counter = 0

    for telem in telem_gen:
        yield telem

        if not camera_enabled:
            continue

        counter += 1

        if counter >= camera_weight:
            counter = 0
            try:
                frame = next(cam_gen)
                yield frame
            except StopIteration:
                print("[UnifiedStream] Camera generator exhausted, disabling camera")
                camera_enabled = False
            except Exception as e:
                print(f"[UnifiedStream] Camera error, disabling camera: {e}")
                camera_enabled = False
