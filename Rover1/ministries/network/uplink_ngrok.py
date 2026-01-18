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
# Adaptive Non-Blocking Send
# ---------------------------------------------------------
def _safe_send(sock, data, max_block_ms=50):
    """
    Attempts to send data with a soft timeout.
    If the socket blocks too long, returns False (drop frame).
    """
    sock.setblocking(False)
    deadline = time.time() + (max_block_ms / 1000.0)

    total_sent = 0
    length = len(data)

    while total_sent < length:
        try:
            sent = sock.send(data[total_sent:])
            if sent == 0:
                return False
            total_sent += sent

        except BlockingIOError:
            if time.time() > deadline:
                return False
            time.sleep(0.001)

        except Exception:
            return False

    return True


# ---------------------------------------------------------
# Telemetry Uplink + Command Downlink (Adaptive)
# ---------------------------------------------------------
def send_telemetry_and_receive_commands(
    generator_factory,
    host="0.tcp.ngrok.io",
    port=12702,
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
            generator = generator_factory()

            # Simple adaptive controls
            dropped_frames = 0
            video_paused_until = 0

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

                        if not _safe_send(sock, hb.encode("utf-8")):
                            print("[Uplink] Heartbeat send blocked — reconnecting")
                            break

                        last_send = now

                    # If uplink is congested, pause video
                    if now < video_paused_until:
                        continue

                    # Encode telemetry or video
                    line = encode_jsonl(obj)
                    payload = line.encode("utf-8")

                    # Telemetry always wins
                    is_video = obj.get("ministry") == "picamera2"

                    # Try sending
                    ok = _safe_send(sock, payload)

                    if not ok:
                        if is_video:
                            dropped_frames += 1
                            print(f"[Uplink] Dropped video frame ({dropped_frames})")

                            # If too many drops → pause video
                            if dropped_frames >= 10:
                                print("[Uplink] Pausing video for 1 second")
                                video_paused_until = now + 1
                                dropped_frames = 0

                            continue  # Do NOT reconnect for video drops

                        # Telemetry failed → reconnect
                        print("[Uplink] Telemetry send blocked — reconnecting")
                        break

                    # Successful send
                    dropped_frames = 0
                    last_send = now
                    print("[Uplink → Host]", line.strip())

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
