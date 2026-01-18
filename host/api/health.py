# host/api/health.py

from host.logs.wrappers import log_watchdog

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

    log_watchdog("watchdog_heartbeat_received", ts=last_heartbeat_ts)

    return {"status": "ok"}


@router.get("/heartbeat_age")
def get_heartbeat_age():
    """
    Returns the age of the last heartbeat.
    """
    if last_heartbeat_ts == 0.0:
        log_watchdog("watchdog_heartbeat_age_requested_none")
        return {"age": None}

    age = time.time() - last_heartbeat_ts
    heartbeat_age_seconds.set(age)

    log_watchdog("watchdog_heartbeat_age_reported", age=age)

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

    log_watchdog(
        "watchdog_health_summary_reported",
        heartbeat_age=summary.get("heartbeat_age_sec"),
        watchdog_age=summary.get("watchdog_age_sec"),
    )

    return summary
    
@router.get("")
def health_root():
    return {"status": "ok"}
