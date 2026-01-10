# services/metrics.py

from prometheus_client import Counter, Gauge, Histogram

# Ingest metrics
ingest_total = Counter("ingest_total", "Total telemetry messages ingested")
ingest_rate = Gauge("ingest_rate", "Messages per second")

# DB metrics
db_queue_depth = Gauge("db_queue_depth", "Length of DB write queue")
db_write_latency = Histogram("db_write_latency_seconds", "DB write latency")

# RF metrics
rf_frames_total = Counter("rf_frames_total", "Total RF frames ingested")
rf_rssi_gauge = Gauge("rf_rssi", "Latest RF RSSI value")

# Heartbeat metrics
heartbeat_age = Gauge("heartbeat_age_seconds", "Seconds since last heartbeat")
watchdog_age = Gauge("watchdog_age_seconds", "Seconds since last watchdog")

# System metrics
uptime_seconds = Gauge("uptime_seconds", "Host uptime in seconds")
