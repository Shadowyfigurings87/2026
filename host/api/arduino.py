from fastapi import APIRouter, HTTPException
from host.logs.wrappers import log_arduino
from host.services import db_reader

router = APIRouter()

# ---------------------------------------------------------
# ARDUINO STATE (DECODED TELEMETRY FROM arduino_state TABLE)
# ---------------------------------------------------------

@router.get("/state")
def get_arduino_state():
    """
    Returns the most recent decoded Arduino telemetry snapshot.
    Pulled from the arduino_state table (single-row UPSERT).
    """
    try:
        state = db_reader.get_latest_arduino_state()

        if not state:
            log_arduino("arduino_state_missing")
            return {
                "status": "unknown",
                "message": "no arduino telemetry available"
            }

        log_arduino("arduino_state_requested", state=state)
        return state

    except Exception as e:
        log_arduino("arduino_state_error", error=str(e))
        raise HTTPException(
            status_code=500,
            detail="Error retrieving Arduino state"
        )


# ---------------------------------------------------------
# RECENT RAW TELEMETRY (UNDECODED)
# ---------------------------------------------------------

@router.get("/recent")
def get_recent_arduino():
    """
    Returns recent raw Arduino telemetry rows from telemetry_raw.
    Useful for debugging or verifying firmware output.
    """
    try:
        rows = db_reader.get_recent_telemetry(limit=100)
        arduino_rows = [r for r in rows if r["ministry"] == "arduino"]

        log_arduino("arduino_recent_requested", count=len(arduino_rows))
        return {"rows": arduino_rows}

    except Exception as e:
        log_arduino("arduino_recent_error", error=str(e))
        raise HTTPException(
            status_code=500,
            detail="Error retrieving recent telemetry"
        )
