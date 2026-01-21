# ingestion/base.py

import time
from datetime import datetime

from ingestion.streams.arduino_stream import arduino_stream
from ingestion.streams.redrover_stream import redrover_stream
from ingestion.streams.heartbeat_stream import heartbeat_stream
from ingestion.streams.watchdog_stream import watchdog_stream

from ingestion.utils.jitter import JitterSmoother
from ingestion.utils.ministry import ensure_ministry
from ingestion.utils.health_logger import log_health

from ingestion.metrics.arduino_metrics import get_arduino_metrics
from ingestion.config import (
    WEIGHTS,
    ARDUINO_METRICS_INTERVAL,
    PRESSURE_LOG_INTERVAL,
    HIGH_PRESSURE_THRESHOLD,
    CRITICAL_PRESSURE_THRESHOLD,
)

from redrover_link.tcp_server import redrover_queue


def merged_stream():
    yield {
        "ministry": "system",
        "event": "startup",
        "ts": time.time(),
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }

    arduino_gen = arduino_stream()
    redrover_gen = redrover_stream()
    hb_gen = heartbeat_stream(interval=5)
    wd_gen = watchdog_stream(check_interval=3)

    smoothers = {
        "arduino": JitterSmoother(),
        "redrover": JitterSmoother(),
        "heartbeat": JitterSmoother(),
        "watchdog": JitterSmoother(),
    }

    last_arduino_metrics_emit = 0
    last_pressure_log = 0

    while True:
        now = time.time()

        # Arduino
        for _ in range(WEIGHTS["arduino"]):
            try:
                obj = next(arduino_gen)
                obj = ensure_ministry(obj, "arduino")
                obj["ts"] = smoothers["arduino"].smooth(obj.get("ts", now))
                obj["timestamp"] = datetime.utcnow().isoformat() + "Z"
                yield obj
            except Exception:
                break

        # Arduino metrics
        if now - last_arduino_metrics_emit > ARDUINO_METRICS_INTERVAL:
            try:
                metrics = get_arduino_metrics()
                metrics = ensure_ministry(metrics, "arduino")
                metrics["event"] = "ministry_metrics"
                metrics["ts"] = smoothers["arduino"].smooth(metrics.get("ts", now))
                metrics["timestamp"] = datetime.utcnow().isoformat() + "Z"
                yield metrics
                log_health("arduino_metrics", metrics)
            except Exception:
                pass
            last_arduino_metrics_emit = now

        # RedRover
        for _ in range(WEIGHTS["redrover"]):
            try:
                obj = next(redrover_gen)
                obj = ensure_ministry(obj, "redrover")
                obj["ts"] = smoothers["redrover"].smooth(obj.get("ts", now))
                obj["_queue_pressure"] = redrover_queue.qsize()
                obj["timestamp"] = datetime.utcnow().isoformat() + "Z"
                yield obj
            except Exception:
                break

        # Heartbeat
        for _ in range(WEIGHTS["heartbeat"]):
            try:
                obj = next(hb_gen)
                obj = ensure_ministry(obj, "heartbeat")
                obj["ts"] = smoothers["heartbeat"].smooth(obj.get("ts", now))
                obj["timestamp"] = datetime.utcnow().isoformat() + "Z"
                yield obj
            except Exception:
                break

        # Watchdog
        for _ in range(WEIGHTS["watchdog"]):
            try:
                obj = next(wd_gen)
                obj = ensure_ministry(obj, "watchdog")
                obj["ts"] = smoothers["watchdog"].smooth(obj.get("ts", now))
                obj["timestamp"] = datetime.utcnow().isoformat() + "Z"
                yield obj
            except Exception:
                break

        time.sleep(0.001)
