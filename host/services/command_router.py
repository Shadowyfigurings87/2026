# host/services/command_router.py

from host.services.connect.command_bus import enqueue_command
from host.logs.wrappers import log_ingest


def send_throttle(value: float):
    """
    Build and enqueue a throttle command.
    """
    cmd = {
        "type": "throttle",
        "value": float(value)
    }
    enqueue_command(cmd)
    log_ingest("command_router_throttle", value=value)
    return cmd


def send_direction(direction: str):
    """
    direction: 'fwd' or 'rev'
    """
    cmd = {
        "type": "direction",
        "dir": direction
    }
    enqueue_command(cmd)
    log_ingest("command_router_direction", direction=direction)
    return cmd


def send_stop():
    cmd = {"type": "stop"}
    enqueue_command(cmd)
    log_ingest("command_router_stop")
    return cmd


def send_custom(payload: dict):
    """
    Accept any custom JSON payload.
    """
    enqueue_command(payload)
    log_ingest("command_router_custom", payload=payload)
    return payload
