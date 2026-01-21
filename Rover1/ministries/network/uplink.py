# Rover1/ministries/network/uplink.py

import threading
import time
import socket

from ministries.utils.jsonl import safe_parse
from ministries.control.motor import handle_command_packet

from .connection import connect_with_retry, safe_send
from .packet_builder import (
    handshake_packet,
    heartbeat_packet,
    telemetry_packet,
)


def _command_listener(sock):
    """
    Reads commands from the host and routes them to the correct ministry.
    Timeout-safe: socket.timeout is normal.
    """

    sock.settimeout(5)

    try:
        with sock, sock.makefile("r") as f:
            while True:
                try:
                    line = f.readline()
                    if not line:
                        print("[Uplink] Listener: host closed connection")
                        break

                    packet = safe_parse(line)
                    if not packet:
                        continue

                    try:
                        handle_command_packet(packet)
                    except Exception as e:
                        print(f"[Uplink] Command handling error: {e}")

                except socket.timeout:
                    continue

                except Exception as e:
                    print(f"[Uplink] Listener fatal error: {e}")
                    break

    except Exception as e:
        print(f"[Uplink] Listener outer error: {e}")


def send_unified_uplink(
    host: str,
    port: int,
    telemetry_generator,
    reconnect_delay: int = 5,
    heartbeat_interval: int = 5,
):
    """
    Hardened unified uplink:
      - One TCP connection
      - Handshake + heartbeat
      - Commands down
      - Telemetry up (from ingestion ministry)
      - Timeout-safe listener
    """

    while True:
        sock = None

        try:
            sock = connect_with_retry(host, port, reconnect_delay=reconnect_delay)

            # Handshake
            hs = handshake_packet()
            print("[Uplink → Host]", hs.strip())
            sock.sendall(hs.encode("utf-8"))

            # Command listener
            listener = threading.Thread(
                target=_command_listener,
                args=(sock,),
                daemon=True,
                name="HostCommandListener",
            )
            listener.start()

            last_send = time.time()
            gen = telemetry_generator

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

                    # Build telemetry packet
                    line = telemetry_packet(obj)
                    payload = line.encode("utf-8")

                    ok = safe_send(sock, payload)
                    if not ok:
                        print("[Uplink] Telemetry send blocked — reconnecting")
                        break

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
