from fastapi import APIRouter, HTTPException, Body
from host.logs.wrappers import log_arduino
from host.services.command_router import (
    send_throttle,
    send_direction,
    send_stop,
    send_custom,
)

# NEW: import the Arduino state pipeline
from host.services.arduino_state import get_latest_arduino_state
from host.services import db_reader

router = APIRouter()


# ---------------------------------------------------------
# ARDUINO STATE (DECODED TELEMETRY)
# ---------------------------------------------------------

@router.get("/state")
def get_arduino_state():
    """
    Returns the most recent decoded Arduino telemetry snapshot.
    """
    try:
        state = get_latest_arduino_state()

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
    Returns recent raw Arduino telemetry rows from SQLite.
    Useful for debugging or verifying firmware output.
    """
    try:
        rows = db_reader.get_recent_arduino_telemetry()
        log_arduino("arduino_recent_requested", count=len(rows))
        return {"rows": rows}

    except Exception as e:
        log_arduino("arduino_recent_error", error=str(e))
        raise HTTPException(
            status_code=500,
            detail="Error retrieving recent telemetry"
        )


# ---------------------------------------------------------
# COMMAND ENDPOINT (UNCHANGED)
# ---------------------------------------------------------

@router.post("/command")
def send_command(payload: dict = Body(...)):
    """
    Accepts a JSON payload and routes it to the correct command function.
    Expected formats:
      { "type": "throttle", "value": 0.5 }
      { "type": "direction", "dir": "fwd" }
      { "type": "stop" }
      { "type": "custom", ... }
    """
    try:
        log_arduino("arduino_command_received", payload=payload)

        cmd_type = payload.get("type")

        if cmd_type == "throttle":
            result = send_throttle(payload.get("value"))

        elif cmd_type == "direction":
            result = send_direction(payload.get("dir"))

        elif cmd_type == "stop":
            result = send_stop()

        else:
            result = send_custom(payload)

        log_arduino("arduino_command_sent", result=result)
        return {"status": "ok", "sent": result}

    except Exception as e:
        log_arduino("arduino_command_error", payload=payload, error=str(e))
        raise HTTPException(
            status_code=500,
            detail="Failed to send Arduino command"
        )
