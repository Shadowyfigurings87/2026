# host/api/command_api.py

from fastapi import APIRouter
from pydantic import BaseModel

from host.services.command_router import (
    send_throttle,
    send_direction,
    send_stop,
    send_custom,
)

router = APIRouter(prefix="/command", tags=["command"])


class ThrottleRequest(BaseModel):
    value: float


class DirectionRequest(BaseModel):
    direction: str  # "fwd" or "rev"


class CustomCommand(BaseModel):
    payload: dict


@router.post("/throttle")
def command_throttle(req: ThrottleRequest):
    cmd = send_throttle(req.value)
    return {"status": "ok", "sent": cmd}


@router.post("/direction")
def command_direction(req: DirectionRequest):
    cmd = send_direction(req.direction)
    return {"status": "ok", "sent": cmd}


@router.post("/stop")
def command_stop():
    cmd = send_stop()
    return {"status": "ok", "sent": cmd}


@router.post("/custom")
def command_custom(req: CustomCommand):
    cmd = send_custom(req.payload)
    return {"status": "ok", "sent": cmd}
