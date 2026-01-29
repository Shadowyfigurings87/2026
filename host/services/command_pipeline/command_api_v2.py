# host/services/command_pipeline/command_api_v2.py

from fastapi import APIRouter
from host.logs.wrappers import log_ingest

from host.services.command_pipeline.command_envelope import wrap_panel_payload
from host.services.command_pipeline.command_ministry import handle_arduino

router = APIRouter()


@router.post("/command")
async def command_api(payload: dict):
    """
    Cockpit → Host command entrypoint.
    Accepts raw cockpit payloads (simple keys like throttle/move/stop),
    wraps them into the sovereign command envelope,
    and routes them to the correct ministry.
    """

    log_ingest("command_received", raw=str(payload))

    # Wrap cockpit payload into sovereign envelope
    enveloped = wrap_panel_payload(payload)
    if not enveloped:
        return {"status": "error", "detail": "Unknown command payload"}

    log_ingest("command_enveloped", envelope=str(enveloped))

    # Route to correct ministry
    ministry = enveloped.get("ministry")

    if ministry == "arduino":
        handle_arduino(enveloped)
        return {"status": "ok", "ministry": "arduino"}

    # Unknown ministry (future-proof)
    log_ingest("unknown_ministry", ministry=str(ministry))
    return {"status": "error", "detail": "Unknown ministry"}
