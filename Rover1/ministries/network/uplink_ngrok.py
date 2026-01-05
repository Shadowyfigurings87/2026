import socket
import threading
import time
import json

from ministries.utils.jsonl import encode_jsonl, safe_parse
from ministries.control.motor import handle_command_packet


# ---------------------------------------------------------
# Command Listener Thread
# ---------------------------------------------------------
def _command_listener(sock):
    """
    Reads commands from the host and routes them to the correct ministry.
    Runs in its own daemon thread.
    """
    try:
        with sock, sock.makefile("r") as f:
            for line in f:
                packet = safe_parse(line)
                if not packet:
                    continue

                # Route host → Rover1 commands
                try:
                    handle_command_packet(packet)
                except Exception as e:
                    print(f"[Uplink] Command handling error: {e}")

    except Exception as e:
        print(f"[Uplink] Listener error: {e}")


# ---------------------------------------------------------
# Telemetry Uplink + Command Downlink
# ---------------------------------------------------------
def send_telemetry_and_receive_commands(
    generator,
    host="4.tcp.ngrok.io",
    port=12479,
    reconnect_delay=5
):
    """
    generator: yields telemetry dicts.
    Host is a TCP server reachable via ngrok.
    """
    while True:
        try:
            print(f"[Uplink] Connecting to host {host}:{port}")

            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            sock.connect((host, port))

            print("[Uplink] Connected to host")
            
            sock.sendall(
                encode_jsonl({"ministry": "uplink", "event": "handshake", "ts": time.time()}).encode("utf-8")
            )

            # Start command listener thread
            listener = threading.Thread(
                target=_command_listener,
                args=(sock,),
                daemon=True,
                name="HostCommandListener"
            )
            listener.start()

            # Send telemetry on same socket
            with sock:
                for obj in generator:
                    try:
                        line = encode_jsonl(obj)
                        sock.sendall(line.encode("utf-8"))
                    except Exception as e:
                        print(f"[Uplink] Telemetry send error: {e}")
                        break  # triggers reconnect

        except Exception as e:
            print(f"[Uplink] Error: {e}, reconnecting in {reconnect_delay}s")
            time.sleep(reconnect_delay)
            continue
