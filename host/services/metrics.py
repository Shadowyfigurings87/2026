# host/services/metrics.py

import time
from prometheus_client import Counter, Gauge, Histogram, REGISTRY

# ============================================================
#  PROMETHEUS METRICS
# ============================================================

# -------- Counters (ever-increasing totals) --------

ingest_total = Counter(
    "rover_ingest_total",
    "Total number of ingestion messages received"
)

rf_frames_total = Counter(
    "rover_rf_frames_total",
    "Total number of RF frames received"
)

db_writes_total = Counter(
    "rover_db_writes_total",
    "Total number of successful DB writes"
)

db_write_errors_total = Counter(
    "rover_db_write_errors_total",
    "Total number of failed DB writes"
)

# -------- Gauges (current values) --------

ingestion_queue_depth = Gauge(
    "rover_ingestion_queue_depth",
    "Current depth of the ingestion queue"
)

rf_frame_rate = Gauge(
    "rover_rf_frame_rate_hz",
    "Estimated RF frame rate (frames per second)"
)

db_write_latency_ms = Gauge(
    "rover_db_write_latency_ms",
    "Latest DB write latency in milliseconds"
)

heartbeat_age_seconds = Gauge(
    "rover_heartbeat_age_seconds",
    "Age of the latest heartbeat in seconds"
)

watchdog_age_seconds = Gauge(
    "rover_watchdog_age_seconds",
    "Age of the latest watchdog update in seconds"
)

# -------- Histograms (latency distributions) --------

db_write_latency_histogram = Histogram(
    "rover_db_write_latency_seconds",
    "DB write latency distribution in seconds",
    buckets=[0.001, 0.005, 0.01, 0.02, 0.05, 0.1, 0.25, 0.5, 1.0]
)

rf_frame_processing_seconds = Histogram(
    "rover_rf_frame_processing_seconds",
    "Time spent processing an RF frame in seconds",
    buckets=[0.001, 0.005, 0.01, 0.02, 0.05, 0.1]
)

# ============================================================
#  HELPER FUNCTIONS FOR API LAYER
# ============================================================

def _get_metric_value(name: str):
    """Safely fetch a Prometheus metric value by name."""
    try:
        value = REGISTRY.get_sample_value(name)
        return value if value is not None else 0.0
    except Exception:
        return 0.0

# ============================================================
#  INGESTION RATE (EPS)
# ============================================================

_last_ingest_count = 0
_last_ingest_time = time.time()

def get_ingestion_rate():
    global _last_ingest_count, _last_ingest_time

    now = time.time()
    current = ingest_total._value.get()

    delta_count = current - _last_ingest_count
    delta_time = now - _last_ingest_time

    if delta_time <= 0:
        return 0.0

    rate = delta_count / delta_time

    _last_ingest_count = current
    _last_ingest_time = now

    return round(rate, 2)

# ============================================================
#  ROVER HEARTBEAT TRACKING
# ============================================================

last_rover_packet_ts = time.time()

def update_rover_heartbeat():
    """Called whenever ANY rover packet arrives."""
    global last_rover_packet_ts
    last_rover_packet_ts = time.time()

def get_rover_heartbeat_age():
    """Seconds since last rover packet."""
    return round(time.time() - last_rover_packet_ts, 2)

# ============================================================
#  ESP32 TELEMETRY (LATEST PACKET)
# ============================================================

latest_esp32_packet = {}
latest_esp32_ts = 0

def update_esp32_packet(packet: dict):
    """Store the latest ESP32 packet in memory."""
    global latest_esp32_packet, latest_esp32_ts
    latest_esp32_packet = packet
    latest_esp32_ts = time.time()

def get_latest_esp32():
    """Return latest ESP32 packet + age."""
    age = round(time.time() - latest_esp32_ts, 2)
    return {
        "packet": latest_esp32_packet,
        "age_seconds": age,
    }

# ============================================================
#  RF + ALFA STATUS HELPERS
# ============================================================

def get_rf_status():
    return {
        "frame_rate_hz": _get_metric_value("rover_rf_frame_rate_hz"),
        "total_frames": _get_metric_value("rover_rf_frames_total"),
    }

def get_alfa_status():
    return {
        "status": "unknown",
        "devices": 0
    }

def get_esp32_status():
    """Placeholder until you add real ESP32 metrics."""
    return {
        "status": "idle",
        "queue_pressure": _get_metric_value("rover_watchdog_age_seconds")
    }
# ============================================================
#  CAMERA FPS TRACKING
# ============================================================

_last_cam_frame_ts = 0
_last_cam_fps_calc_ts = time.time()
_cam_frame_counter = 0
_cam_fps = 0.0

def update_camera_frame():
    """
    Called every time a camera frame is ingested.
    """
    global _last_cam_frame_ts, _cam_frame_counter
    _last_cam_frame_ts = time.time()
    _cam_frame_counter += 1

def get_camera_fps():
    """
    Returns rolling FPS based on frames counted in the last second.
    """
    global _last_cam_fps_calc_ts, _cam_frame_counter, _cam_fps

    now = time.time()
    delta = now - _last_cam_fps_calc_ts

    if delta >= 1.0:
        _cam_fps = _cam_frame_counter / delta
        _cam_frame_counter = 0
        _last_cam_fps_calc_ts = now

    return round(_cam_fps, 2)

def get_camera_last_frame_age():
    """
    Seconds since the last camera frame was received.
    """
    if _last_cam_frame_ts == 0:
        return None
    return round(time.time() - _last_cam_frame_ts, 2)
