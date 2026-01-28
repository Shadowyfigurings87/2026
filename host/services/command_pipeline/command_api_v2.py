from fastapi import APIRouter
from host.services.command_pipeline.command_ministry import handle_command

router = APIRouter(prefix="/commands", tags=["commands"])

@router.post("/send")
def send_command(payload: dict):
    handle_command(payload)
    return {"status": "ok", "received": payload}
