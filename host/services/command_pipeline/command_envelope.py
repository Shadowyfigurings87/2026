# host/services/command_pipeline/command_envelope.py

import time

def wrap_panel_payload(raw):
    ts = int(time.time())

    # THROTTLE
    if "throttle" in raw:
        return {
            "ministry": "arduino",
            "cmd": "throttle",
            "value": raw["throttle"],
            "ts": ts
        }

    # MOVE
    if "move" in raw:
        return {
            "ministry": "arduino",
            "cmd": "move",
            "value": raw["move"],
            "ts": ts
        }

    # STOP
    if "stop" in raw:
        return {
            "ministry": "arduino",
            "cmd": "stop",
            "value": None,
            "ts": ts
        }

    # ACTUATOR
    if "actuator" in raw:
        return {
            "ministry": "arduino",
            "cmd": "actuator",
            "value": raw["actuator"],
            "ts": ts
        }

    print("Unknown cockpit payload:", raw)
    return None
