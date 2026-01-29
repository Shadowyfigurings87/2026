# ministries/network/command_client.py

import socket
import time
import json
import traceback

from Rover1.ministries.arduino.commands import send_arduino_command
from Rover1.ministries.control.motor import apply_motor_command


# ============================================================
# CONFIG
# ============================================================

COMMAND_HOST = "8.tcp.ngrok.io"     # Dedicated command tunnel host
COMMAND_PORT = 15822                # Dedicated command tunnel port

RECONNECT_DELAY = 3.0               # Seconds between reconnect attempts
BUFFER_SIZE = 4096                  # Socket read size


# ============================================================
# DISPATCH TABLE
# ============================================================

def dispatch_command(cmd: dict):
    """
    Route incoming commands to the correct Rover1 ministry.
    """
    print(f"[CommandClient] DISPATCH → {cmd}")

    try:
        kind = cmd.get("cmd")
        print(f"[CommandClient] Command kind = {kind}")

        # -------------------------------
        # Motor control
        # -------------------------------
        if kind == "drive":
            throttle = cmd.get("throttle", 0)
            direction = cmd.get("direction", "stop")
            print(f"[CommandClient] Dispatching DRIVE → throttle={throttle}, direction={direction}")
            apply_motor_command(throttle, direction)
            return

        # -------------------------------
        # Arduino passthrough
        # -------------------------------
        if kind == "arduino":
            payload = cmd.get("payload")
            print(f"[CommandClient] Dispatching ARDUINO → payload={payload}")
            if payload:
                send_arduino_command(payload)
            return

        # -------------------------------
        # System commands
        # -------------------------------
        if kind == "ping":
            print("[CommandClient] Received ping")
            return

        # -------------------------------
        # Unknown command
        # -------------------------------
        print(f"[CommandClient] Unknown command received: {cmd}")

    except Exception as e:
        print(f"[CommandClient] ERROR executing command: {e}")
        traceback.print_exc()


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
        print("[CommandClient] CONNECTED to Host command server")
        return sock
    except Exception as e:
        print(f"[CommandClient] Connection FAILED: {e}")
        return None


def listen_for_commands(sock: socket.socket):
    """
    Read line-delimited JSON commands from the Host.
    """
    print("[CommandClient] Listening for commands…")
    buffer = ""

    while True:
        try:
            data = sock.recv(BUFFER_SIZE)

            # -------------------------------
            # Connection closed
            # -------------------------------
            if not data:
                print("[CommandClient] Host CLOSED connection")
                return

            print(f"[CommandClient] RAW DATA RECEIVED: {data!r}")

            # Decode and append to buffer
            decoded = data.decode("utf-8", errors="ignore")
            print(f"[CommandClient] DECODED DATA: {decoded!r}")
            buffer += decoded

            # -------------------------------
            # Process complete lines
            # -------------------------------
            while "\n" in buffer:
                line, buffer = buffer.split("\n", 1)
                print(f"[CommandClient] LINE EXTRACTED: {line!r}")

                if not line.strip():
                    print("[CommandClient] Skipping empty line")
                    continue

                try:
                    cmd = json.loads(line)
                    print(f"[CommandClient] JSON PARSED OK: {cmd}")
                    dispatch_command(cmd)
                except Exception as e:
                    print(f"[CommandClient] ERROR parsing JSON line: {line!r}")
                    traceback.print_exc()

        except socket.timeout:
            # Normal idle condition
            continue

        except Exception as e:
            print(f"[CommandClient] SOCKET ERROR: {e}")
            traceback.print_exc()
            return


# ============================================================
# MAIN LOOP
# ============================================================

def start_command_client():
    """
    Persistent loop: connect → listen → reconnect.
    """
    print("[CommandClient] Ministry STARTING…")

    while True:
        sock = connect_to_host()

        if sock:
            listen_for_commands(sock)

        print(f"[CommandClient] RECONNECTING in {RECONNECT_DELAY} seconds…")
        time.sleep(RECONNECT_DELAY)
