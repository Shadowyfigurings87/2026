from host.services.command_pipeline.command_server import command_server

current_throttle = 0

def handle_command(payload: dict):
    global current_throttle

    # -----------------------------
    # THROTTLE
    # -----------------------------
    if "throttle" in payload:
        value = int(payload["throttle"])
        current_throttle = value
        command_server.send_line(f"PWM:{value}")
        return

    # -----------------------------
    # MOVE (FWD / REV)
    # -----------------------------
    if "move" in payload:
        move = payload["move"]
        if move == "forward":
            command_server.send_line("DIR:FWD")
            command_server.send_line(f"PWM:{current_throttle}")
        elif move == "reverse":
            command_server.send_line("DIR:REV")
            command_server.send_line(f"PWM:{current_throttle}")
        return

    # -----------------------------
    # STOP
    # -----------------------------
    if "stop" in payload:
        command_server.send_line("PWM:0")
        command_server.send_line("ACT:STOP")
        return

    # -----------------------------
    # ACTUATOR STEERING
    # -----------------------------
    if "actuator" in payload:
        act = payload["actuator"]
        direction = act.get("dir")
        speed = int(act.get("speed", 0))

        if direction == "FWD":
            command_server.send_line(f"ACT:FWD:{speed}")
        elif direction == "REV":
            command_server.send_line(f"ACT:REV:{speed}")
        return

    # -----------------------------
    # MODE (crawl / cruise / boost)
    # -----------------------------
    if "mode" in payload:
        mode = payload["mode"]
        print("Mode set:", mode)
        return

    # -----------------------------
    # UNKNOWN
    # -----------------------------
    print("Unknown command payload:", payload)
