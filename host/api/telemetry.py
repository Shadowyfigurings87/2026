from host.logs.logging import info
from fastapi import APIRouter, Response
from typing import List
from host.schemas import TelemetryRecord
from host.services import db_reader

router = APIRouter()

@router.get("/recent", response_model=List[TelemetryRecord])
def get_recent():
    return db_reader.get_recent_telemetry()
# host/api/system.py (example)
