# Rover1/ministries/network/connection.py

import socket
import time


def connect_with_retry(host, port, reconnect_delay=5):
    """
    Connect to the host with retry logic.
    Hardened for Rover1 uplink:
      - Infinite retry loop
      - Clear logging
      - 10s timeout to avoid hangs
      - Returns a live socket ready for use
    """

    while True:
        try:
            print(f"[Uplink] Connecting to {host}:{port}…")
            sock = socket.create_connection((host, port), timeout=10)

            # Disable Nagle for low-latency telemetry
            sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)

            print("[Uplink] Connected")
            return sock

        except Exception as e:
            print(f"[Uplink] Connection failed: {e}")
            print(f"[Uplink] Retrying in {reconnect_delay}s")
            time.sleep(reconnect_delay)


def safe_send(sock, data: bytes) -> bool:
    """
    Send data safely. Returns False if the socket is blocked or broken.

    This function is intentionally minimal:
      - No exceptions propagate
      - No partial sends
      - No retries here (uplink handles reconnect)
    """

    try:
        sock.sendall(data)
        return True

    except Exception:
        return False
