from host.logs.logging import info, warn, error

def _log(ministry, event, fields):
    # Remove ministry if already present to avoid duplicate keyword errors
    fields.pop("ministry", None)
    info(event, ministry=ministry, **fields)

def log_ingest(event, **fields):
    _log("ingestion", event, fields)

def log_rf(event, **fields):
    _log("rf", event, fields)

def log_arduino(event, **fields):
    _log("arduino", event, fields)

def log_esp32(event, **fields):
    _log("esp32", event, fields)

def log_camera(event, **fields):
    _log("camera", event, fields)

def log_watchdog(event, **fields):
    _log("watchdog", event, fields)

def log_system(event, **fields):
    _log("system", event, fields)
