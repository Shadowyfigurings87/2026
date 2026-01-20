# host/api/command_api.py

from fastapi import APIRouter
from pydantic import BaseModel

from host.services.command_router import enqueue_command
from host.logs.wrappers import log_ingest

router = APIRouter(prefix="/command", tags=["command"])


# ---------------------------------------------------------
# REQUEST MODELS
# ---------------------------------------------------------

class ThrottleRequest(BaseModel):
    value: float


class DirectionRequest(BaseModel):
    direction: str  # "fwd" or "rev"


class StopRequest(BaseModel):
    reason: str | None = None


class CustomCommand(BaseModel):
    payload: dict


# ---------------------------------------------------------
# COMMAND ENDPOINTS
# ---------------------------------------------------------

@router.post("/throttle")
def command_throttle(req: ThrottleRequest):
    cmd = {"type": "throttle", "value": req.value}
    enqueue_command(cmd)
    log_ingest("command_api_throttle", value=req.value)
    return {"status": "ok", "sent": cmd}


@router.post("/direction")
def command_direction(req: DirectionRequest):
    cmd = {"type": "direction", "dir": req.direction}
    enqueue_command(cmd)
    log_ingest("command_api_direction", direction=req.direction)
    return {"status": "ok", "sent": cmd}


@router.post("/stop")
def command_stop(req: StopRequest | None = None):
    cmd = {"type": "stop", "reason": req.reason if req else None}
    enqueue_command(cmd)
    log_ingest("command_api_stop", reason=cmd.get("reason"))
    return {"status": "ok", "sent": cmd}


@router.post("/custom")
def command_custom(req: CustomCommand):
    enqueue_command(req.payload)
    log_ingest("command_api_custom", payload=req.payload)
    return {"status": "ok", "sent": req.payload}
