# host/api/telemetry.py

from fastapi import APIRouter
from typing import List
from host.schemas import TelemetryRecord
from host.services import db_reader
from host.services.connect.worker import ingestion_queue
from host.services.metrics import ingestion_queue_depth
from host.services.metrics import get_ingestion_rate
from host.services.metrics import get_rover_heartbeat_age

router = APIRouter(prefix="/telemetry", tags=["telemetry"])

@router.get("/queue_depth")
def get_queue_depth():
    return {
        "queue_depth": ingestion_queue.qsize(),
        "metric_depth": ingestion_queue_depth._value.get()
    }

@router.get("/recent", response_model=List[TelemetryRecord])
def get_recent():
    return db_reader.get_recent_telemetry()

@router.get("/arduino/latest")
def get_arduino_latest():
    state = db_reader.get_arduino_state() or {}
    return {
        "rpm": state.get("rpm"),
        "throttle": state.get("throttle"),
        "direction": state.get("direction"),
        "voltage": state.get("voltage", None),
        "temp": state.get("temp", None),
    }

@router.get("/arduino/rpm")
def get_arduino_rpm():
    state = db_reader.get_arduino_state()
    if not state:
        return {"rpm": 0}
    return {"rpm": state.get("rpm", 0)}

@router.get("/arduino/state")
def get_arduino_state():
    return db_reader.get_arduino_state() or {}

@router.get("/ingestion_rate")
def ingestion_rate():
    return {"ingestion_rate": get_ingestion_rate()}

@router.get("/rover_heartbeat")
def rover_heartbeat():
    return {"age_seconds": get_rover_heartbeat_age()}
