# ministries/ingestion/base.py

import time
from datetime import datetime

from Rover1.ministries.ingestion.streams.arduino_stream import arduino_ingest_stream
from Rover1.ministries.ingestion.streams.redrover_stream import redrover_stream
from Rover1.ministries.ingestion.streams.heartbeat_stream import heartbeat_stream
from Rover1.ministries.ingestion.streams.watchdog_stream import watchdog_stream

from Rover1.ministries.ingestion.utils.jitter import JitterSmoother
from Rover1.ministries.ingestion.utils.ministry import ensure_ministry
from Rover1.ministries.ingestion.utils.health_logger import log_health

from Rover1.ministries.ingestion.metrics.arduino_metrics import get_arduino_metrics
from Rover1.ministries.ingestion.config import (
    WEIGHTS,
    ARDUINO_METRICS_INTERVAL,
    PRESSURE_LOG_INTERVAL,
    HIGH_PRESSURE_THRESHOLD,
    CRITICAL_PRESSURE_THRESHOLD,
)

from Rover1.redrover_link.tcp_server import redrover_queue

# NEW: GPS SQL query
from Rover1.db.gps_query import get_latest_gps


print(f"[Ingestion] base.py loaded from: {__file__}")


def _iso_now():
    return datetime.utcnow().isoformat() + "Z"


def merged_stream():
    """
    Unified ingestion generator:
      - Arduino ministry events
      - RedRover events
      - Heartbeat events
      - Watchdog events
      - Arduino ministry metrics
      - GPS telemetry (from SQL)
      - Queue pressure monitoring

    This is the single source of truth for the uplink ministry.
    """

    # Initial startup event
    startup_evt = {
        "ministry": "system",
        "event": "startup",
        "ts": time.time(),
        "timestamp": _iso_now(),
    }
    print("[Ingestion] Emitting startup event:", startup_evt)
    yield startup_evt

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
        "gps": JitterSmoother(),   # NEW smoother
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
            except StopIteration:
                print("[Ingestion] Arduino generator exhausted")
                break
            except Exception as e:
                print(f"[Ingestion] Arduino generator exception: {e}")
                break

            if obj is None:
                continue

            obj = ensure_ministry(obj, "arduino")
            obj["ts"] = smoothers["arduino"].smooth(obj.get("ts", now))
            obj["timestamp"] = _iso_now()
            print("[Ingestion] Arduino event:", obj)
            yield obj

        # ---------------------------------------------------------
        # Arduino ministry metrics
        # ---------------------------------------------------------
        if now - last_arduino_metrics_emit > ARDUINO_METRICS_INTERVAL:
            try:
                metrics = get_arduino_metrics()
                metrics = ensure_ministry(metrics, "arduino")
                metrics["event"] = "ministry_metrics"
                metrics["ts"] = smoothers["arduino"].smooth(metrics.get("ts", now))
                metrics["timestamp"] = _iso_now()
                print("[Ingestion] Arduino metrics:", metrics)
                yield metrics
                log_health("arduino_metrics", metrics)
            except Exception as e:
                print(f"[Ingestion] Arduino metrics error: {e}")

            last_arduino_metrics_emit = now

        # ---------------------------------------------------------
        # RedRover telemetry
        # ---------------------------------------------------------
        for _ in range(WEIGHTS["redrover"]):
            try:
                obj = next(redrover_gen)
            except StopIteration:
                break
            except Exception as e:
                print(f"[Ingestion] RedRover generator exception: {e}")
                break

            if obj is None:
                continue

            obj = ensure_ministry(obj, "redrover")
            obj["ts"] = smoothers["redrover"].smooth(obj.get("ts", now))
            try:
                obj["_queue_pressure"] = redrover_queue.qsize()
            except Exception:
                obj["_queue_pressure"] = None
            obj["timestamp"] = _iso_now()
            print("[Ingestion] RedRover event:", obj)
            yield obj

        # ---------------------------------------------------------
        # GPS telemetry (from SQL)
        # ---------------------------------------------------------
        try:
            gps_row = get_latest_gps()
            if gps_row:
                ts, lat, lon = gps_row
                gps_obj = {
                    "ministry": "gps",
                    "event": "position",
                    "ts": smoothers["gps"].smooth(ts),
                    "timestamp": _iso_now(),
                    "lat": lat,
                    "lon": lon,
                }
                print("[Ingestion] GPS event:", gps_obj)
                yield gps_obj
        except Exception as e:
            print(f"[Ingestion] GPS query error: {e}")

        # ---------------------------------------------------------
        # Queue pressure logging
        # ---------------------------------------------------------
        if now - last_pressure_log > PRESSURE_LOG_INTERVAL:
            try:
                qsize = redrover_queue.qsize()
            except Exception:
                qsize = None

            if qsize is not None:
                if qsize > CRITICAL_PRESSURE_THRESHOLD:
                    level = "CRITICAL"
                elif qsize > HIGH_PRESSURE_THRESHOLD:
                    level = "HIGH"
                else:
                    level = "NORMAL"

                print(
                    f"[Ingestion] Queue pressure: size={qsize} level={level} "
                    f"(HIGH={HIGH_PRESSURE_THRESHOLD}, CRITICAL={CRITICAL_PRESSURE_THRESHOLD})"
                )

            last_pressure_log = now

        # ---------------------------------------------------------
        # Heartbeat events
        # ---------------------------------------------------------
        for _ in range(WEIGHTS["heartbeat"]):
            try:
                obj = next(hb_gen)
            except StopIteration:
                print("[Ingestion] Heartbeat generator exhausted")
                break
            except Exception as e:
                print(f"[Ingestion] Heartbeat generator exception: {e}")
                break

            if obj is None:
                continue

            obj = ensure_ministry(obj, "heartbeat")
            obj["ts"] = smoothers["heartbeat"].smooth(obj.get("ts", now))
            obj["timestamp"] = _iso_now()
            print("[Ingestion] Heartbeat event:", obj)
            yield obj

        # ---------------------------------------------------------
        # Watchdog events
        # ---------------------------------------------------------
        for _ in range(WEIGHTS["watchdog"]):
            try:
                obj = next(wd_gen)
            except StopIteration:
                print("[Ingestion] Watchdog generator exhausted")
                break
            except Exception as e:
                print(f"[Ingestion] Watchdog generator exception: {e}")
                break

            if obj is None:
                continue

            obj = ensure_ministry(obj, "watchdog")
            obj["ts"] = smoothers["watchdog"].smooth(obj.get("ts", now))
            obj["timestamp"] = _iso_now()
            print("[Ingestion] Watchdog event:", obj)
            yield obj

        # ---------------------------------------------------------
        # Loop pacing
        # ---------------------------------------------------------
        time.sleep(0.001)
