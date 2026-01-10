# host/api/health.py

import time
from fastapi import APIRouter

from host.services import db_reader
from host.services.metrics import (
    heartbeat_age_seconds,
    watchdog_age_seconds,
)

from host.schemas import HealthStatus

router = APIRouter()

# ---------------------------------------------------------
# IN-MEMORY HEARTBEAT TRACKING
# ---------------------------------------------------------

last_heartbeat_ts = 0.0


@router.post("/heartbeat")
def receive_heartbeat():
    """
    Rover sends a heartbeat ping.
    """
    global last_heartbeat_ts
    last_heartbeat_ts = time.time()
    heartbeat_age_seconds.set(0.0)
    return {"status": "ok"}


@router.get("/heartbeat_age")
def get_heartbeat_age():
    """
    Returns the age of the last heartbeat.
    """
    if last_heartbeat_ts == 0.0:
        return {"age": None}

    age = time.time() - last_heartbeat_ts
    heartbeat_age_seconds.set(age)
    return {"age": age}


# ---------------------------------------------------------
# DB-BACKED HEALTH SUMMARY
# ---------------------------------------------------------

@router.get("/summary", response_model=HealthStatus)
def get_health_summary():
    """
    Returns heartbeat + watchdog ages from SQLite.
    """
    summary = db_reader.get_health_summary()

    # Update Prometheus metrics
    if summary["heartbeat_age_sec"] is not None:
        heartbeat_age_seconds.set(summary["heartbeat_age_sec"])

    if summary["watchdog_age_sec"] is not None:
        watchdog_age_seconds.set(summary["watchdog_age_sec"])

    return summary
