# Rover1/ministries/network/uplink.py

import threading
import time

from ministries.utils.jsonl import safe_parse
from ministries.control.motor import handle_command_packet

from .connection import connect_with_retry, safe_send
from .packet_builder import (
    handshake_packet,
    heartbeat_packet,
    telemetry_packet,
    camera_packet,
)
from .streams import unified_stream_with_camera


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


def send_unified_uplink(
    host: str,
    port: int,
    reconnect_delay: int = 5,
    heartbeat_interval: int = 5,
    camera_fps: int = 10,
    camera_weight: int = 5,
):
    """
    Unified uplink:
      - one TCP connection
      - handshake + heartbeat
      - commands down
      - telemetry up (arduino, redrover, heartbeat, watchdog)
      - camera frames up (picamera2)
    """

    while True:
        sock = None

        try:
            # Connect (with retry)
            sock = connect_with_retry(host, port, reconnect_delay=reconnect_delay)

            # Handshake (now using ministry="system")
            hs = handshake_packet()
            print("[Uplink → Host]", hs.strip())
            sock.sendall(hs.encode("utf-8"))

            # Command listener thread
            listener = threading.Thread(
                target=_command_listener,
                args=(sock,),
                daemon=True,
                name="HostCommandListener",
            )
            listener.start()

            last_send = time.time()
            dropped_frames = 0
            video_paused_until = 0

            # Unified stream: telemetry + camera
            gen = unified_stream_with_camera(
                camera_fps=camera_fps,
                camera_weight=camera_weight,
            )

            with sock:
                for obj in gen:
                    now = time.time()

                    # Heartbeat if quiet
                    if now - last_send > heartbeat_interval:
                        hb = heartbeat_packet()
                        print("[Uplink → Host]", hb.strip())
                        if not safe_send(sock, hb.encode("utf-8")):
                            print("[Uplink] Heartbeat blocked — reconnecting")
                            break
                        last_send = now

                    is_video = obj.get("ministry") == "picamera2"

                    if is_video:
                        if now < video_paused_until:
                            continue
                        line = camera_packet(obj)
                    else:
                        line = telemetry_packet(obj)

                    payload = line.encode("utf-8")
                    ok = safe_send(sock, payload)

                    if not ok:
                        if is_video:
                            dropped_frames += 1
                            print(f"[Uplink] Dropped video frame ({dropped_frames})")
                            if dropped_frames >= 10:
                                print("[Uplink] Pausing video for 1 second")
                                video_paused_until = now + 1
                                dropped_frames = 0
                            continue

                        print("[Uplink] Telemetry send blocked — reconnecting")
                        break

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
