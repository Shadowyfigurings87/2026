# host/services/connect/esp32_handler.py

from host.logs.logging import info
from host.services import db_writer
from host.services.metrics import update_esp32_packet, update_rover_heartbeat


def handle_esp32_json(payload: dict) -> None:
    """
    Process a single ESP32 JSON telemetry payload.

    Expected payload example:
    {
        "ministry": "esp32",
        "ts": 1768630594.003703,
        "timestamp": "2026-01-18T02:17:21.169163Z",
        "status": "idle" | "active" | "error",
        "_queue_pressure": 14088
    }
    """

    # Normalize fields
    status = payload.get("status") or "unknown"
    queue_pressure = payload.get("_queue_pressure")
    ts = payload.get("timestamp") or payload.get("ts")

    # Update heartbeat (ESP32 packets count as rover activity)
    update_rover_heartbeat()

    # Update in-memory ESP32 packet for dashboard
    update_esp32_packet(payload)

    # Log ingestion event
    info(
        "esp32_ingest",
        ministry="esp32",
        status=status,
        queue_pressure=queue_pressure,
        ts=ts,
    )

    # Persist latest ESP32 state in DB
    db_writer.upsert_esp32_state(
        status=status,
        queue_pressure=queue_pressure,
        ts=ts,
        raw=payload,
    )
