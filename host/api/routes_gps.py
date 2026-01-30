# host/api/routes_gps.py

from fastapi import APIRouter
from host.services.db_reader import get_latest_gps, get_gps_history

router = APIRouter(prefix="/gps", tags=["gps"])


@router.get("/latest")
def gps_latest():
    row = get_latest_gps()
    if not row:
        return {"status": "no_data"}
    return {"status": "ok", **row}


@router.get("/history")
def gps_history(limit: int = 500):
    rows = get_gps_history(limit=limit)
    return {
        "status": "ok",
        "count": len(rows),
        "points": rows,
    }
