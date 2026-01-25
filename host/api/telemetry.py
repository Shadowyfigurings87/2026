# host/api/telemetry.py

from fastapi import APIRouter
from typing import List
from host.schemas import TelemetryRecord
from host.services import db_reader
from host.services.connect.worker import ingestion_queue
from host.services.metrics import (
    ingestion_queue_depth,
    get_ingestion_rate,
    get_rover_heartbeat_age,
)

router = APIRouter(prefix="/telemetry", tags=["telemetry"])


# ===============================
# QUEUE + INGESTION METRICS
# ===============================

@router.get("/queue_depth")
def get_queue_depth():
    return {
        "queue_depth": ingestion_queue.qsize(),
        "metric_depth": ingestion_queue_depth._value.get(),
    }


@router.get("/ingestion_rate")
def ingestion_rate():
    return {"ingestion_rate": get_ingestion_rate()}


@router.get("/rover_heartbeat")
def rover_heartbeat():
    return {"age_seconds": get_rover_heartbeat_age()}


# ===============================
# RAW TELEMETRY
# ===============================

@router.get("/recent", response_model=List[TelemetryRecord])
def get_recent():
    return db_reader.get_recent_telemetry()


@router.get("/raw/latest")
def get_raw_latest():
    return db_reader.get_latest_raw() or {}


# ===============================
# ARDUINO TELEMETRY (DECODED)
# ===============================

@router.get("/arduino/latest")
def get_arduino_latest():
    """
    Returns the latest decoded Arduino state from arduino_state.
    This is the canonical 2026 ministry output.
    """
    state = db_reader.get_latest_arduino_state() or {}
    return {
        "rpm": state.get("rpm"),
        "throttle": state.get("throttle"),
        "direction": state.get("direction"),
        "pwm": state.get("pwm"),
        "ts": state.get("ts"),
        "raw": state.get("raw"),
    }


@router.get("/arduino/rpm")
def get_arduino_rpm():
    state = db_reader.get_latest_arduino_state() or {}
    return {"rpm": state.get("rpm")}


@router.get("/arduino/state")
def get_arduino_state():
    """
    Full decoded Arduino state.
    """
    return db_reader.get_latest_arduino_state() or {}


# ===============================
# ESP32 TELEMETRY
# ===============================

@router.get("/esp32/latest")
def get_esp32_latest():
    return db_reader.get_esp32_state() or {}


# ===============================
# UNIFIED TELEMETRY SNAPSHOT
# ===============================

@router.get("/latest")
def get_latest_unified():
    """
    Returns a unified snapshot of the latest telemetry from all ministries.
    Perfect for dashboards and cockpit panels.
    """
    return {
        "arduino": db_reader.get_latest_arduino_state() or {},
        "esp32": db_reader.get_esp32_state() or {},
        "heartbeat_age": get_rover_heartbeat_age(),
        "queue_depth": ingestion_queue.qsize(),
        "ingestion_rate": get_ingestion_rate(),
        "raw": db_reader.get_latest_raw() or {},
    }
