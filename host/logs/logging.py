import json
import time
import sys

def log(level, event, ministry=None, **fields):
    entry = {
        "ts": time.time(),
        "level": level,
        "event": event,
    }

    if ministry:
        entry["ministry"] = ministry

    entry.update(fields)

    sys.stdout.write(json.dumps(entry) + "\n")
    sys.stdout.flush()

def info(event, ministry=None, **fields):
    log("INFO", event, ministry, **fields)

def warn(event, ministry=None, **fields):
    log("WARN", event, ministry, **fields)

def error(event, ministry=None, **fields):
    log("ERROR", event, ministry, **fields)
