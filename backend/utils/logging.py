import json
import logging
import os
import sys
from datetime import datetime
from logging.handlers import TimedRotatingFileHandler

# Ensure logs directory exists
LOG_DIR = os.path.join(os.path.dirname(__file__), "..", "logs")
os.makedirs(LOG_DIR, exist_ok=True)

# Log file paths
MAIN_LOG = os.path.join(LOG_DIR, "backend.log")
ERROR_LOG = os.path.join(LOG_DIR, "backend-error.log")
WARNING_LOG = os.path.join(LOG_DIR, "backend-warning.log")
METRICS_LOG = os.path.join(LOG_DIR, "backend-metrics.log")

# Configure root logger
logger = logging.getLogger("backend")
logger.setLevel(logging.DEBUG)

# Console handler (stdout)
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.DEBUG)

# Rotating file handlers
main_handler = TimedRotatingFileHandler(
    MAIN_LOG, when="midnight", interval=1, backupCount=7, encoding="utf-8"
)
main_handler.setLevel(logging.DEBUG)

error_handler = TimedRotatingFileHandler(
    ERROR_LOG, when="midnight", interval=1, backupCount=14, encoding="utf-8"
)
error_handler.setLevel(logging.ERROR)

warning_handler = TimedRotatingFileHandler(
    WARNING_LOG, when="midnight", interval=1, backupCount=14, encoding="utf-8"
)
warning_handler.setLevel(logging.WARNING)

metrics_handler = TimedRotatingFileHandler(
    METRICS_LOG, when="midnight", interval=1, backupCount=30, encoding="utf-8"
)
metrics_handler.setLevel(logging.INFO)

# Formatter: structured JSON
class JSONFormatter(logging.Formatter):
    def format(self, record):
        entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "component": getattr(record, "component", "system"),
            "severity": record.levelname,
            "event": getattr(record, "event", record.msg),
            "details": getattr(record, "details", {}),
        }
        return json.dumps(entry)

formatter = JSONFormatter()
console_handler.setFormatter(formatter)
main_handler.setFormatter(formatter)
error_handler.setFormatter(formatter)
warning_handler.setFormatter(formatter)
metrics_handler.setFormatter(formatter)

# Attach handlers
logger.addHandler(console_handler)
logger.addHandler(main_handler)
logger.addHandler(error_handler)
logger.addHandler(warning_handler)
logger.addHandler(metrics_handler)


def log_event(component, severity, event, details=None):
    """
    Unified structured logging for all ministries.
    severity: DEBUG, INFO, WARNING, ERROR, CRITICAL
    """
    level = getattr(logging, severity.upper(), logging.INFO)
    extra = {"component": component, "event": event, "details": details or {}}
    logger.log(level, event, extra=extra)
