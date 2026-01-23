# ingestion/base.py

import time
from datetime import datetime

from ministries.ingestion.streams.arduino_stream import arduino_ingest_stream
from ministries.ingestion.streams.redrover_stream import redrover_stream
from ministries.ingestion.streams.heartbeat_stream import heartbeat_stream
from ministries.ingestion.streams.watchdog_stream import watchdog_stream

from ministries.ingestion.utils.jitter import JitterSmoother
from ministries.ingestion.utils.ministry import ensure_ministry
from ministries.ingestion.utils.health_logger import log_health

from ministries.ingestion.metrics.arduino_metrics import get_arduino_metrics
from ministries.ingestion.config import (
    WEIGHTS,
    ARDUINO_METRICS_INTERVAL,
    PRESSURE_LOG_INTERVAL,
    HIGH_PRESSURE_THRESHOLD,
    CRITICAL_PRESSURE_THRESHOLD,
)

from redrover_link.tcp_server import redrover_queue


def merged_stream():
    """
    Unified ingestion generator:
      - Arduino ministry events
      - RedRover events
      - Heartbeat events
      - Watchdog events
      - Arduino ministry metrics
      - Queue pressure monitoring

    This is the single source of truth for the uplink ministry.
    """

    # Initial startup event
    yield {
        "ministry": "system",
        "event": "startup",
        "ts": time.time(),
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }

    # Initialize generators
    arduino_gen = arduino_ingest_stream()
    redrover_gen = redrover_stream()
    hb_gen = heartbeat_stream(interval=5)
    wd_gen = watchdog_stream(check_interval=3)

    # Jitter smoothers per ministry
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

        # ---------------------------------------------------------
        # Arduino telemetry
        # ---------------------------------------------------------
        for _ in range(WEIGHTS["arduino"]):
            try:
                obj = next(arduino_gen)
                obj = ensure_ministry(obj, "arduino")
                obj["ts"] = smoothers["arduino"].smooth(obj.get("ts", now))
                obj["timestamp"] = datetime.utcnow().isoformat() + "Z"
                yield obj
            except Exception:
                break

        # ---------------------------------------------------------
        # Arduino ministry metrics
        # ---------------------------------------------------------
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

        # ---------------------------------------------------------
        # RedRover telemetry
        # ---------------------------------------------------------
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

        # ---------------------------------------------------------
        # Heartbeat events
        # ---------------------------------------------------------
        for _ in range(WEIGHTS["heartbeat"]):
            try:
                obj = next(hb_gen)
                obj = ensure_ministry(obj, "heartbeat")
                obj["ts"] = smoothers["heartbeat"].smooth(obj.get("ts", now))
                obj["timestamp"] = datetime.utcnow().isoformat() + "Z"
                yield obj
            except Exception:
                break

        # ---------------------------------------------------------
        # Watchdog events
        # ---------------------------------------------------------
        for _ in range(WEIGHTS["watchdog"]):
            try:
                obj = next(wd_gen)
                obj = ensure_ministry(obj, "watchdog")
                obj["ts"] = smoothers["watchdog"].smooth(obj.get("ts", now))
                obj["timestamp"] = datetime.utcnow().isoformat() + "Z"
                yield obj
            except Exception:
                break

        # ---------------------------------------------------------
        # Loop pacing
        # ---------------------------------------------------------
        time.sleep(0.001)
