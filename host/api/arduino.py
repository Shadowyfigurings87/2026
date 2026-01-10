from fastapi import APIRouter

router = APIRouter()

@router.get("/state")
def get_arduino_state():
    return {"status": "ok", "message": "arduino endpoint online"}
