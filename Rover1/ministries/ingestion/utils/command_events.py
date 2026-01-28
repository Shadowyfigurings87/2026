import time
from Rover1.ministries.ingestion.base import push_event

def emit_command_event(cmd: dict, status: str = "received"):
    """
    Emit a command telemetry event into the ingestion pipeline.
    """
    event = {
        "ministry": "command",
        "ts": time.time(),
        "status": status,
        "command": cmd,
    }

    push_event(event)
