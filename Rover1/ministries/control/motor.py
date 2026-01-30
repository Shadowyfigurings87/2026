# Rover1/ministries/control/motor.py

from Rover1.ministries.arduino.commands import send_arduino_command

# ============================================================
# INTERNAL MOTOR STATE
# ============================================================

_current_pwm = 0
_current_direction = "stop"


# ============================================================
# SAFETY HELPERS
# ============================================================

def _safe_set_direction(new_direction: str):
    global _current_direction, _current_pwm

    # Prevent direction changes at high throttle
    if _current_pwm > 30 and new_direction != _current_direction:
        print(f"[Motor] BLOCKED direction change: {_current_direction} → {new_direction} at PWM={_current_pwm}")
        return False

    if new_direction == "forward":
        send_arduino_command("DIR:FWD")

    elif new_direction == "reverse":
        send_arduino_command("DIR:REV")

    elif new_direction == "stop":
        send_arduino_command("ACT:STOP")
        send_arduino_command("PWM:0")
        _current_pwm = 0
        _current_direction = "stop"
        return True

    else:
        print(f"[Motor] Invalid direction: {new_direction}")
        return False

    _current_direction = new_direction
    return True


def _set_pwm(pwm_value: int):
    global _current_pwm
    pwm_value = max(0, min(pwm_value, 255))
    send_arduino_command(f"PWM:{pwm_value}")
    _current_pwm = pwm_value


# ============================================================
# PUBLIC MOTOR MINISTRY ENTRY POINT
# ============================================================

def apply_motor_command(throttle: float | None, direction: str | None):
    """
    Unified motor control interface for the new command pipeline.

    throttle: 0.0 → 1.0 or None
    direction:
        "forward"  → set forward
        "reverse"  → set reverse
        "stop"     → stop immediately
        None       → keep current direction
    """

    global _current_direction

    # ---------------------------------------------------------
    # STOP overrides everything
    # ---------------------------------------------------------
    if direction == "stop":
        print("[Motor] STOP command received")
        _safe_set_direction("stop")
        return

    # ---------------------------------------------------------
    # If direction is explicitly given, update it
    # ---------------------------------------------------------
    if direction is not None:
        if not _safe_set_direction(direction):
            print("[Motor] Direction change blocked for safety")
            return
        print(f"[Motor] Direction updated to {_current_direction}")

    # ---------------------------------------------------------
    # Apply PWM only if throttle is provided
    # ---------------------------------------------------------
    if throttle is not None:
        throttle = max(0.0, min(throttle, 1.0))
        pwm_value = int(throttle * 255)
        _set_pwm(pwm_value)
        print(f"[Motor] Applied: direction={_current_direction}, pwm={pwm_value}")
    else:
        print(f"[Motor] No throttle change, direction={_current_direction}")


# ============================================================
# LEGACY SUPPORT
# ============================================================

def handle_command_packet(packet):
    print("[Motor] Legacy command packet received (deprecated):", packet)
