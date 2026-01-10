from fastapi import APIRouter

router = APIRouter()

@router.get("/recent")
def get_recent_rf():
    return {"status": "ok", "message": "rf endpoint online"}
