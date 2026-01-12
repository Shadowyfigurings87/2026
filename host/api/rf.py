# host/api/rf.py

from fastapi import APIRouter
from host.logs.wrappers import log_rf

router = APIRouter()

@router.get("/recent")
def get_recent_rf():
    # Example if you ever want to log:
    # log_rf("rf_recent_requested")
    return {"status": "ok", "message": "rf endpoint online"}
