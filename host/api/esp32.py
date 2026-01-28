from fastapi import APIRouter
from host.services import db_reader

router = APIRouter(tags=["esp32"])

@router.get("")
def get_esp32_status():
    state = db_reader.get_esp32_state()
    if not state:
        return {
            "status": "unknown",
            "queue_pressure": None,
            "ts": None,
            "raw": None,
        }

    return {
        "status": state.get("status"),
        "queue_pressure": state.get("queue_pressure"),
        "ts": state.get("ts"),
        "raw": state.get("raw"),
    }
