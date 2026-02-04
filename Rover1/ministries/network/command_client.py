# ministries/network/command_client.py

import socket
import time
import json
import traceback
import sys
import inspect
import threading

# Import modules, NOT functions — prevents circular import corruption
import Rover1.ministries.arduino.commands as arduino_commands
import Rover1.ministries.control.motor as motor


# ============================================================
# GLOBAL DEBUG HELPERS
# ============================================================

def _debug_header(label: str):
    print("\n" + "=" * 60)
    print(f"[CommandClient/DEBUG] {label}")
    print("=" * 60)


def _debug_ministry_state(context: str):
    print(f"[CommandClient/DEBUG] Context: {context}")
    print(f"[CommandClient/DEBUG] Thread: {threading.current_thread().name}")

    # Motor module + function
    try:
        print(f"[CommandClient/DEBUG] motor module path: {getattr(motor, '__file__', 'NO __file__')}")
        print(f"[CommandClient/DEBUG] motor object: {motor} (type={type(motor)})")
        print(f"[CommandClient/DEBUG] motor.apply_motor_command: {getattr(motor, 'apply_motor_command', None)} "
              f"(type={type(getattr(motor, 'apply_motor_command', None))})")
    except Exception as e:
        print(f"[CommandClient/DEBUG] ERROR inspecting motor: {e}")
        traceback.print_exc()

    # Arduino commands module + function
    try:
        print(f"[CommandClient/DEBUG] arduino_commands module path: {getattr(arduino_commands, '__file__', 'NO __file__')}")
        print(f"[CommandClient/DEBUG] arduino_commands object: {arduino_commands} (type={type(arduino_commands)})")
        print(f"[CommandClient/DEBUG] arduino_commands.send_arduino_command: "
              f"{getattr(arduino_commands, 'send_arduino_command', None)} "
              f"(type={type(getattr(arduino_commands, 'send_arduino_command', None))})")
    except Exception as e:
        print(f"[CommandClient/DEBUG] ERROR inspecting arduino_commands: {e}")
        traceback.print_exc()


# ============================================================
# STARTUP DEBUG
# ============================================================

_debug_header("IMPORT + ENVIRONMENT")
print("[CommandClient/DEBUG] sys.executable:", sys.executable)
print("[CommandClient/DEBUG] sys.path:", sys.path)

print("[CommandClient/DEBUG] motor module path:", getattr(motor, "__file__", "NO __file__"))
print("[CommandClient/DEBUG] motor.apply_motor_command:", getattr(motor, "apply_motor_command", None),
      "type:", type(getattr(motor, "apply_motor_command", None)))

print("[CommandClient/DEBUG] arduino_commands module path:", getattr(arduino_commands, "__file__", "NO __file__"))
print("[CommandClient/DEBUG] arduino_commands.send_arduino_command:",
      getattr(arduino_commands, "send_arduino_command", None),
      "type:", type(getattr(arduino_commands, "send_arduino_command", None)))


# ============================================================
# CONFIG
# ============================================================

COMMAND_HOST = "6.tcp.ngrok.io"
COMMAND_PORT = 14064

RECONNECT_DELAY = 3.0
BUFFER_SIZE = 4096


# ============================================================
# DISPATCH TABLE
# ============================================================

def dispatch_command(cmd: dict):
    """
    Route incoming commands to the correct Rover1 ministry.
    """
    _debug_header("DISPATCH ENTRY")
    print(f"[CommandClient] DISPATCH → {cmd}")
    _debug_ministry_state("before dispatch_command() routing")

    try:
        kind = cmd.get("cmd")
        print(f"[CommandClient] Command kind = {kind}")

        # ======================================================
        # THROTTLE MINISTRY
        # ======================================================
        if kind == "throttle":
            value = cmd.get("value", 0)
            print(f"[CommandClient] THROTTLE → raw value={value}")

            throttle_float = max(0.0, min(value / 255.0, 1.0))
            print(f"[CommandClient] THROTTLE → normalized={throttle_float}")

            _debug_ministry_state("before THROTTLE motor.apply_motor_command()")
            print(f"[CommandClient] Calling motor.apply_motor_command(throttle={throttle_float}, direction=None)")
            motor.apply_motor_command(throttle_float, None)
            print(f"[CommandClient] apply_motor_command() returned OK")
            _debug_ministry_state("after THROTTLE motor.apply_motor_command()")
            return

        # ======================================================
        # MOVE / DIRECTION MINISTRY
        # ======================================================
        if kind == "move":
            direction = cmd.get("value", "stop")
            print(f"[CommandClient] MOVE → {direction}")

            _debug_ministry_state("before MOVE motor.apply_motor_command()")
            print(f"[CommandClient] Calling motor.apply_motor_command(throttle=None, direction={direction})")
            motor.apply_motor_command(None, direction)
            print(f"[CommandClient] apply_motor_command() returned OK")
            _debug_ministry_state("after MOVE motor.apply_motor_command()")
            return

        # ======================================================
        # GLOBAL STOP
        # ======================================================
        if kind == "stop":
            print("[CommandClient] GLOBAL STOP → calling motor.apply_motor_command(None, 'stop')")
            _debug_ministry_state("before STOP motor.apply_motor_command()")
            motor.apply_motor_command(None, "stop")
            print("[CommandClient] STOP completed")
            _debug_ministry_state("after STOP motor.apply_motor_command()")
            return

        # ======================================================
        # ACTUATOR MINISTRY
        # ======================================================
        if kind == "actuator":
            direction = cmd.get("dir", "STOP")
            speed = cmd.get("speed", 0)
            payload = f"ACT:{direction}:{speed}"

            print(f"[CommandClient] ACTUATOR → {payload}")
            _debug_ministry_state("before ACTUATOR arduino_commands.send_arduino_command()")
            print(f"[CommandClient] Calling arduino_commands.send_arduino_command({payload})")
            arduino_commands.send_arduino_command(payload)
            print("[CommandClient] Actuator command sent")
            _debug_ministry_state("after ACTUATOR arduino_commands.send_arduino_command()")
            return

        # ======================================================
        # RAW ARDUINO PASSTHROUGH
        # ======================================================
        if kind == "arduino":
            payload = cmd.get("payload")
            print(f"[CommandClient] ARDUINO PASSTHROUGH → {payload}")

            if payload:
                _debug_ministry_state("before ARDUINO PASSTHROUGH arduino_commands.send_arduino_command()")
                print(f"[CommandClient] Calling arduino_commands.send_arduino_command({payload})")
                arduino_commands.send_arduino_command(payload)
                print("[CommandClient] Arduino passthrough sent")
                _debug_ministry_state("after ARDUINO PASSTHROUGH arduino_commands.send_arduino_command()")
            else:
                print("[CommandClient] WARNING: Arduino passthrough missing payload")
            return

        # ======================================================
        # LEGACY DRIVE COMMAND
        # ======================================================
        if kind == "drive":
            throttle = cmd.get("throttle", 0)
            direction = cmd.get("direction", "stop")

            print(f"[CommandClient] DRIVE (legacy) → throttle={throttle}, direction={direction}")
            _debug_ministry_state("before LEGACY DRIVE motor.apply_motor_command()")
            print(f"[CommandClient] Calling motor.apply_motor_command({throttle}, {direction})")
            motor.apply_motor_command(throttle, direction)
            print("[CommandClient] Legacy drive completed")
            _debug_ministry_state("after LEGACY DRIVE motor.apply_motor_command()")
            return

        # ======================================================
        # SYSTEM PING
        # ======================================================
        if kind == "ping":
            print("[CommandClient] Received ping")
            _debug_ministry_state("PING (no-op)")
            return

        # ======================================================
        # UNKNOWN COMMAND
        # ======================================================
        print(f"[CommandClient] ERROR: Unknown command received → {cmd}")
        _debug_ministry_state("UNKNOWN COMMAND")

    except Exception as e:
        print(f"[CommandClient] ERROR executing command: {e}")
        traceback.print_exc()
        _debug_ministry_state("EXCEPTION in dispatch_command()")


# ============================================================
# SOCKET LOOP
# ============================================================

def connect_to_host():
    _debug_header("CONNECT TO HOST")
    print(f"[CommandClient] Connecting to {COMMAND_HOST}:{COMMAND_PORT}…")
    _debug_ministry_state("before connect_to_host()")

    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        print("[CommandClient] Socket created:", sock)
        sock.connect((COMMAND_HOST, COMMAND_PORT))
        print("[CommandClient] Socket connected")
        sock.settimeout(1.0)
        print("[CommandClient] Socket timeout set to 1.0s")
        print("[CommandClient] CONNECTED to Host command server")
        _debug_ministry_state("after successful connect_to_host()")
        return sock
    except Exception as e:
        print(f"[CommandClient] Connection FAILED: {e}")
        traceback.print_exc()
        _debug_ministry_state("connect_to_host() FAILED")
        return None


def listen_for_commands(sock: socket.socket):
    _debug_header("LISTEN FOR COMMANDS")
    print("[CommandClient] Listening for commands…")
    _debug_ministry_state("enter listen_for_commands()")

    buffer = ""

    while True:
        try:
            print("[CommandClient] Waiting for data from socket…")
            data = sock.recv(BUFFER_SIZE)

            if not data:
                print("[CommandClient] Host CLOSED connection")
                _debug_ministry_state("socket closed by host")
                return

            print(f"[CommandClient] RAW DATA RECEIVED: {data!r}")

            decoded = data.decode("utf-8", errors="ignore")
            print(f"[CommandClient] DECODED DATA: {decoded!r}")

            buffer += decoded
            print(f"[CommandClient] BUFFER STATE (len={len(buffer)}): {buffer!r}")

            while "\n" in buffer:
                line, buffer = buffer.split("\n", 1)
                print(f"[CommandClient] LINE EXTRACTED: {line!r}")
                print(f"[CommandClient] REMAINING BUFFER (len={len(buffer)}): {buffer!r}")

                if not line.strip():
                    print("[CommandClient] Skipping empty line")
                    continue

                try:
                    cmd = json.loads(line)
                    print(f"[CommandClient] JSON PARSED OK: {cmd}")
                    _debug_ministry_state("before dispatch_command() call from listen_for_commands()")
                    dispatch_command(cmd)
                    _debug_ministry_state("after dispatch_command() call from listen_for_commands()")
                except Exception as e:
                    print(f"[CommandClient] ERROR parsing JSON line: {line!r}")
                    traceback.print_exc()
                    _debug_ministry_state("JSON PARSE ERROR in listen_for_commands()")

        except socket.timeout:
            continue

        except Exception as e:
            print(f"[CommandClient] SOCKET ERROR: {e}")
            traceback.print_exc()
            _debug_ministry_state("SOCKET ERROR in listen_for_commands()")
            return


# ============================================================
# MAIN LOOP
# ============================================================

def start_command_client():
    _debug_header("COMMAND CLIENT MAIN LOOP")
    print("[CommandClient] Ministry STARTING…")
    _debug_ministry_state("enter start_command_client()")

    while True:
        sock = connect_to_host()

        if sock:
            listen_for_commands(sock)

        print(f"[CommandClient] RECONNECTING in {RECONNECT_DELAY} seconds…")
        _debug_ministry_state("before reconnect sleep in start_command_client()")
        time.sleep(RECONNECT_DELAY)
