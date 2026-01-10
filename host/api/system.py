# host/api/system.py

import time
from fastapi import APIRouter
from host.services.metrics import watchdog_age_seconds

router = APIRouter()

# ---------------------------------------------------------
# SYSTEM STATS ENDPOINT
# ---------------------------------------------------------

@router.get("/stats")
def get_system_stats():
    return {"status": "ok", "message": "system endpoint online"}


# ---------------------------------------------------------
# WATCHDOG TRACKING
# ---------------------------------------------------------

last_watchdog_ts = 0.0


@router.post("/watchdog")
def update_watchdog():
    """
    Called by the rover or another ministry to signal liveness.
    """
    global last_watchdog_ts
    last_watchdog_ts = time.time()
    watchdog_age_seconds.set(0.0)
    return {"status": "ok"}


@router.get("/watchdog_age")
def get_watchdog_age():
    """
    Returns the age of the last watchdog update.
    """
    if last_watchdog_ts == 0.0:
        return {"age": None}

    age = time.time() - last_watchdog_ts
    watchdog_age_seconds.set(age)
    return {"age": age}
