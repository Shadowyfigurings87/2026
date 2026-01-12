# host/services/metrics.py

from prometheus_client import Counter, Gauge, Histogram

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
