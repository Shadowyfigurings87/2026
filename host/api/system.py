from fastapi import APIRouter

router = APIRouter()

@router.get("/stats")
def get_system_stats():
    return {"status": "ok", "message": "system endpoint online"}
