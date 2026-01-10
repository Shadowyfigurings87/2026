from fastapi import APIRouter
from typing import List
from schemas import TelemetryRecord
from services import db_reader

router = APIRouter()

@router.get("/recent", response_model=List[TelemetryRecord])
def get_recent():
    return db_reader.get_recent_telemetry()
