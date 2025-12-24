import socket
import threading
from ministries.utils.jsonl import encode_jsonl, safe_parse
from ministries.control.motor import handle_command_packet

def _command_listener(sock):
    with sock, sock.makefile("r") as f:
        for line in f:
            packet = safe_parse(line)
            if not packet:
                continue
            # host → Rover1 commands
            handle_command_packet(packet)

def send_telemetry_and_receive_commands(generator,
                                         host="127.0.0.1",
                                         port=6000,
                                         reconnect_delay=5):
    """
    generator: yields telemetry dicts.
    Host is a TCP server reachable via ngrok.
    """
    import time

    while True:
        try:
            print(f"[Uplink] Connecting to host {host}:{port}")
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((host, port))

            # Listen for commands in a thread
            t = threading.Thread(target=_command_listener, args=(sock,), daemon=True)
            t.start()

            # Send telemetry on same socket
            with sock:
                for obj in generator:
                    line = encode_jsonl(obj)
                    sock.sendall(line.encode("utf-8"))
        except Exception as e:
            print(f"[Uplink] Error: {e}, reconnecting in {reconnect_delay}s")
            time.sleep(reconnect_delay)
            continue
