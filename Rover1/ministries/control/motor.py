from arduino import write_to_arduino

# ---------------------------------------------------------
# Entry point for host → Rover1 commands
# ---------------------------------------------------------
def handle_command_packet(packet):
    """
    Expected packet examples:
      { "ministry":"control", "action":"actuator", "direction":"forward", "speed":120 }
      { "ministry":"control", "action":"pwm", "value":180 }
      { "ministry":"control", "action":"direction", "value":"reverse" }
    """
    if packet.get("ministry") != "control":
        return

    action = packet.get("action")

    if action == "actuator":
        return _handle_actuator(packet)

    if action == "pwm":
        return _handle_pwm(packet)

    if action == "direction":
        return _handle_direction(packet)

    print(f"[Motor] Unknown action: {action}")


# ---------------------------------------------------------
# BTS7960 Actuator Control
# ---------------------------------------------------------
def _handle_actuator(packet):
    direction = packet.get("direction", "").lower()
    speed = int(packet.get("speed", 0))
    speed = max(0, min(speed, 255))

    if direction == "forward":
        cmd = f"ACT:FWD:{speed}"
    elif direction == "reverse":
        cmd = f"ACT:REV:{speed}"
    elif direction == "stop":
        cmd = "ACT:STOP"
    else:
        print(f"[Motor] Invalid actuator direction: {direction}")
        return

    print(f"[Motor] → Arduino: {cmd}")
    write_to_arduino(cmd)


# ---------------------------------------------------------
# PWM Spindle / Motor Control
# ---------------------------------------------------------
def _handle_pwm(packet):
    value = int(packet.get("value", 0))
    value = max(0, min(value, 255))

    cmd = f"PWM:{value}"
    print(f"[Motor] → Arduino: {cmd}")
    write_to_arduino(cmd)


# ---------------------------------------------------------
# Optocoupler Direction Control
# ---------------------------------------------------------
def _handle_direction(packet):
    value = packet.get("value", "").lower()

    if value == "forward":
        cmd = "DIR:FWD"
    elif value == "reverse":
        cmd = "DIR:REV"
    else:
        print(f"[Motor] Invalid direction value: {value}")
        return

    print(f"[Motor] → Arduino: {cmd}")
    write_to_arduino(cmd)
