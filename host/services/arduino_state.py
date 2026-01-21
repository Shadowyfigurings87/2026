# host/services/arduino_state.py

import json
from host.services import db_reader
from host.services.arduino_decoder import decode_arduino_line

def get_latest_arduino_state():
    """
    Fetches the latest Arduino telemetry row from telemetry_raw,
    decodes it, and returns structured state.
    """
    row = db_reader.get_latest_arduino_raw()
    if not row:
        return None

    payload = json.loads(row["payload"])
    raw_line = payload.get("raw", "")

    decoded = decode_arduino_line(raw_line)
    return decoded
