# host/services/command_pipeline/command_ministry.py

import json
from host.services.command_pipeline.command_server import command_server

current_throttle = 0

def handle_arduino(cmd: dict):
    """
    Sovereign Arduino command handler.
    Accepts structured JSON commands and forwards them as JSON
    over the command tunnel. Rover1 will parse the JSON and
    translate into ASCII for the Arduino.
    """

    global current_throttle

    action = cmd.get("cmd")
    value = cmd.get("value")

    # ---------------------------------------------------------
    # THROTTLE  (value = integer PWM)
    # ---------------------------------------------------------
    if action == "throttle":
        throttle = int(value)
        current_throttle = throttle

        payload = {
            "cmd": "throttle",
            "value": throttle
        }
        command_server.send_line(json.dumps(payload))
        return

    # ---------------------------------------------------------
    # MOVE (forward / reverse)
    # ---------------------------------------------------------
    if action == "move":
        direction = value  # "forward" or "reverse"

        payload = {
            "cmd": "move",
            "value": direction,
            "throttle": current_throttle
        }
        command_server.send_line(json.dumps(payload))
        return

    # ---------------------------------------------------------
    # STOP (hard stop)
    # ---------------------------------------------------------
    if action == "stop":
        payload = {
            "cmd": "stop"
        }
        command_server.send_line(json.dumps(payload))
        return

    # ---------------------------------------------------------
    # ACTUATOR STEERING
    # value = { "dir": "FWD"|"REV", "speed": int }
    # ---------------------------------------------------------
    if action == "actuator":
        direction = value.get("dir")
        speed = int(value.get("speed", 0))

        payload = {
            "cmd": "actuator",
            "dir": direction,
            "speed": speed
        }
        command_server.send_line(json.dumps(payload))
        return

    # ---------------------------------------------------------
    # UNKNOWN COMMAND
    # ---------------------------------------------------------
    print("Unknown Arduino command:", cmd)
