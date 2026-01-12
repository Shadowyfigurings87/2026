# host/api/arduino.py

from fastapi import APIRouter, HTTPException
from host.logs.wrappers import log_arduino
from host.services import db_reader

router = APIRouter()

# ---------------------------------------------------------
# ARDUINO STATE (IN-MEMORY OR DB-BACKED)
# ---------------------------------------------------------

@router.get("/state")
def get_arduino_state():
    """
    Returns the most recent Arduino telemetry snapshot.
    This is frontend-friendly and safe to call frequently.
    """
    try:
        state = db_reader.get_latest_arduino_state()

        if not state:
            log_arduino("arduino_state_missing")
            return {"status": "unknown", "message": "no arduino state available"}

        log_arduino("arduino_state_requested", state=state)
        return state

    except Exception as e:
        log_arduino("arduino_state_error", error=str(e))
        raise HTTPException(status_code=500, detail="Error retrieving Arduino state")


# ---------------------------------------------------------
# RAW TELEMETRY (OPTIONAL)
# ---------------------------------------------------------

@router.get("/recent")
def get_recent_arduino():
    """
    Returns recent Arduino telemetry rows from SQLite.
    Useful for debugging or advanced UI panels.
    """
    try:
        rows = db_reader.get_recent_arduino_telemetry()

        log_arduino("arduino_recent_requested", count=len(rows))
        return {"rows": rows}

    except Exception as e:
        log_arduino("arduino_recent_error", error=str(e))
        raise HTTPException(status_code=500, detail="Error retrieving recent telemetry")
