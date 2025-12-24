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

# ------------------------------------------------------------
# 1. Create backend logger
# ------------------------------------------------------------
backend_logger = logging.getLogger("backend")
backend_logger.setLevel(logging.DEBUG)
backend_logger.propagate = True

# ------------------------------------------------------------
# 2. Create console handler
# ------------------------------------------------------------
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.DEBUG)

# ------------------------------------------------------------
# 3. Reset root logger so it doesn't swallow logs
# ------------------------------------------------------------
root = logging.getLogger()
root.handlers.clear()
root.setLevel(logging.DEBUG)
root.addHandler(console_handler)
root.propagate = False

# ------------------------------------------------------------
# 4. Create file handlers
# ------------------------------------------------------------
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

# ------------------------------------------------------------
# 5. Create JSON formatter and attach to all handlers
# ------------------------------------------------------------
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

# ------------------------------------------------------------
# 6. Attach file handlers to backend logger
# ------------------------------------------------------------
backend_logger.addHandler(main_handler)
backend_logger.addHandler(error_handler)
backend_logger.addHandler(warning_handler)
backend_logger.addHandler(metrics_handler)

# ------------------------------------------------------------
# 7. log_event helper
# ------------------------------------------------------------
def log_event(component, severity, event, details=None):
    level = getattr(logging, severity.upper(), logging.INFO)
    extra = {"component": component, "event": event, "details": details or {}}
    backend_logger.log(level, event, extra=extra)
