import socket
import threading
import time
from datetime import datetime

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

                try:
                    handle_command_packet(packet)
                except Exception as e:
                    print(f"[Uplink] Command handling error: {e}")

    except Exception as e:
        print(f"[Uplink] Listener error: {e}")


# ---------------------------------------------------------
# TCP Keepalive Configuration
# ---------------------------------------------------------
def _configure_keepalive(sock: socket.socket):
    """
    Configure aggressive TCP keepalive so dead links are detected quickly.
    """
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
    sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPIDLE, 10)
    sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPINTVL, 5)
    sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPCNT, 3)


# ---------------------------------------------------------
# Telemetry Uplink + Command Downlink (Resilient)
# ---------------------------------------------------------
def send_telemetry_and_receive_commands(
    generator_factory,   # 🔥 CHANGED: now expects a factory, not a generator
    host="4.tcp.ngrok.io",
    port=14846,
    reconnect_delay=5,
    heartbeat_interval=5,
):
    """
    generator_factory: a callable that returns a fresh generator.
    """

    while True:
        sock = None

        try:
            print(f"[Uplink] Connecting to host {host}:{port}")

            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            _configure_keepalive(sock)

            sock.connect((host, port))
            print("[Uplink] Connected to host")

            # Send handshake
            handshake = encode_jsonl({
                "ministry": "uplink",
                "event": "handshake",
                "ts": time.time(),
                "timestamp": datetime.utcnow().isoformat() + "Z"
            })

            print("[Uplink → Host]", handshake.strip())
            sock.sendall(handshake.encode("utf-8"))

            # Start command listener thread
            listener = threading.Thread(
                target=_command_listener,
                args=(sock,),
                daemon=True,
                name="HostCommandListener"
            )
            listener.start()

            # Telemetry + heartbeat loop
            last_send = time.time()

            # 🔥 NEW: create a fresh generator for this connection
            generator = generator_factory()

            with sock:
                for obj in generator:
                    now = time.time()

                    # Heartbeat if quiet
                    if now - last_send > heartbeat_interval:
                        hb = encode_jsonl({
                            "ministry": "uplink",
                            "event": "heartbeat",
                            "ts": now,
                            "timestamp": datetime.utcnow().isoformat() + "Z"
                        })

                        print("[Uplink → Host]", hb.strip())

                        try:
                            sock.sendall(hb.encode("utf-8"))
                            last_send = now
                        except Exception as e:
                            print(f"[Uplink] Heartbeat send error: {e}")
                            break

                    # Send telemetry
                    try:
                        line = encode_jsonl(obj)
                        print("[Uplink → Host]", line.strip())
                        sock.sendall(line.encode("utf-8"))
                        last_send = now

                    except Exception as e:
                        print(f"[Uplink] Telemetry send error: {e}")
                        break  # triggers reconnect

            print(f"[Uplink] Socket closed, reconnecting in {reconnect_delay}s")

        except Exception as e:
            print(f"[Uplink] Error: {e}, reconnecting in {reconnect_delay}s")

        finally:
            if sock is not None:
                try:
                    sock.close()
                except Exception:
                    pass

            time.sleep(reconnect_delay)
