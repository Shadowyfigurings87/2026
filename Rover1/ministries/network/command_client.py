import socket
import time
import json
import traceback

from Rover1.ministries.arduino.commands import send_arduino_command
from Rover1.ministries.control.motor import apply_motor_command

# Telemetry emission
from Rover1.ministries.ingestion.base import push_event


# ============================================================
# CONFIG
# ============================================================

COMMAND_HOST = "2.tcp.ngrok.io"     # Replace with your command tunnel host
COMMAND_PORT = 18237                # Replace with your command tunnel port

RECONNECT_DELAY = 3.0               # Seconds between reconnect attempts
BUFFER_SIZE = 4096                  # Socket read size


# ============================================================
# TELEMETRY EMISSION
# ============================================================

def emit_command_event(cmd: dict, status: str):
    """
    Emit a command telemetry event into the ingestion pipeline.
    """
    event = {
        "ministry": "command",
        "ts": time.time(),
        "status": status,
        "command": cmd,
    }
    push_event(event)


# ============================================================
# DISPATCH TABLE
# ============================================================

def dispatch_command(cmd: dict):
    """
    Route incoming commands to the correct Rover1 ministry.
    Emits telemetry for received/executed/error states.
    """
    emit_command_event(cmd, status="received")

    try:
        kind = cmd.get("cmd")

        # -------------------------------
        # Motor control
        # -------------------------------
        if kind == "drive":
            throttle = cmd.get("throttle", 0)
            direction = cmd.get("direction", "stop")
            apply_motor_command(throttle, direction)
            emit_command_event(cmd, status="executed")
            return

        # -------------------------------
        # Arduino passthrough
        # -------------------------------
        if kind == "arduino":
            payload = cmd.get("payload")
            if payload:
                send_arduino_command(payload)
            emit_command_event(cmd, status="executed")
            return

        # -------------------------------
        # System commands
        # -------------------------------
        if kind == "ping":
            print("[CommandClient] Received ping")
            emit_command_event(cmd, status="executed")
            return

        # -------------------------------
        # Unknown command
        # -------------------------------
        print(f"[CommandClient] Unknown command: {cmd}")
        emit_command_event(cmd, status="unknown_command")

    except Exception as e:
        print(f"[CommandClient] ERROR executing command: {e}")
        traceback.print_exc()
        emit_command_event(cmd, status=f"error:{e}")


# ============================================================
# SOCKET LOOP
# ============================================================

def connect_to_host():
    """
    Attempt to connect to the Host command server.
    Returns a connected socket or None.
    """
    try:
        print(f"[CommandClient] Connecting to {COMMAND_HOST}:{COMMAND_PORT}…")
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((COMMAND_HOST, COMMAND_PORT))
        sock.settimeout(1.0)
        print("[CommandClient] Connected to Host command server")
        return sock
    except Exception as e:
        print(f"[CommandClient] Connection failed: {e}")
        return None


def listen_for_commands(sock: socket.socket):
    """
    Read line-delimited JSON commands from the Host.
    """
    buffer = ""

    while True:
        try:
            data = sock.recv(BUFFER_SIZE)
            if not data:
                print("[CommandClient] Host closed connection")
                return

            buffer += data.decode("utf-8", errors="ignore")

            # Process complete lines
            while "\n" in buffer:
                line, buffer = buffer.split("\n", 1)
                if not line.strip():
                    continue

                try:
                    cmd = json.loads(line)
                    dispatch_command(cmd)
                except Exception:
                    print("[CommandClient] Error parsing command:")
                    traceback.print_exc()

        except socket.timeout:
            continue
        except Exception as e:
            print(f"[CommandClient] Socket error: {e}")
            return


# ============================================================
# MAIN LOOP
# ============================================================

def start_command_client():
    """
    Persistent loop: connect → listen → reconnect.
    """
    print("[CommandClient] Ministry starting…")

    while True:
        sock = connect_to_host()
        if sock:
            listen_for_commands(sock)

        print(f"[CommandClient] Reconnecting in {RECONNECT_DELAY} seconds…")
        time.sleep(RECONNECT_DELAY)
