# Rover1/ministries/control/motor.py

from Rover1.ministries.arduino.commands import send_arduino_command


# ============================================================
# NEW unified motor command entry point
# ============================================================

def apply_motor_command(throttle: float, direction: str):
    """
    Unified motor control interface for the new command pipeline.

    throttle: 0.0 → 1.0
    direction: "forward", "reverse", "stop"
    """

    # Clamp throttle
    throttle = max(0.0, min(throttle, 1.0))
    pwm_value = int(throttle * 255)

    # ---------------------------------------------------------
    # Direction control
    # ---------------------------------------------------------
    if direction == "forward":
        send_arduino_command("DIR:FWD")
    elif direction == "reverse":
        send_arduino_command("DIR:REV")
    elif direction == "stop":
        send_arduino_command("ACT:STOP")
        send_arduino_command("PWM:0")
        return
    else:
        print(f"[Motor] Invalid direction: {direction}")
        return

    # ---------------------------------------------------------
    # PWM control
    # ---------------------------------------------------------
    send_arduino_command(f"PWM:{pwm_value}")

    print(f"[Motor] Applied: direction={direction}, pwm={pwm_value}")


# ============================================================
# Legacy compatibility (optional)
# ============================================================

def handle_command_packet(packet):
    """
    Legacy support for old ingestion-based motor commands.
    Not used by the new command client.
    """
    print("[Motor] Legacy command packet received (deprecated):", packet)
