from host.logs.logging import info, warn, error

def log_rf(event, **fields):
    info(event, ministry="rf", **fields)

def log_ingest(event, **fields):
    info(event, ministry="ingestion", **fields)

def log_camera(event, **fields):
    info(event, ministry="camera", **fields)

def log_arduino(event, **fields):
    info(event, ministry="arduino", **fields)

def log_db(event, **fields):
    info(event, ministry="db", **fields)

def log_watchdog(event, **fields):
    info(event, ministry="watchdog", **fields)

def log_api(event, **fields):
    info(event, ministry="api", **fields)
