# ingestion/config.py

WEIGHTS = {
    "arduino": 3,
    "redrover": 2,
    "heartbeat": 1,
    "watchdog": 1,
}

ARDUINO_METRICS_INTERVAL = 5
PRESSURE_LOG_INTERVAL = 5

HIGH_PRESSURE_THRESHOLD = 500
CRITICAL_PRESSURE_THRESHOLD = 1000
