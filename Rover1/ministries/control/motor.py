from arduino import arduino_command_queue

def enqueue_motor_command(direction, speed):
    """
    direction: 'FWD' or 'REV' or 'STOP'
    speed: 0-255
    """
    cmd = {
        "type": "motor",
        "direction": direction,
        "speed": int(speed),
    }
    arduino_command_queue.put(cmd)

def handle_command_packet(packet):
    """
    packet: dict from host, e.g.
    {"kind":"command","target":"motor","direction":"FWD","speed":120}
    """
    if packet.get("kind") != "command":
        return

    target = packet.get("target")
    if target == "motor":
        direction = packet.get("direction", "STOP")
        speed = packet.get("speed", 0)
        enqueue_motor_command(direction, speed)
