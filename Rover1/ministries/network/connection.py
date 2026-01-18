# Rover1/ministries/network/connection.py
#
# Hardened TCP connection helpers:
# - connect_with_retry
# - safe_send

import socket
import time


def connect_with_retry(host, port, reconnect_delay=5, timeout=10):
    """
    Connect to (host, port) with retry.
    Blocks until a connection is established.
    """
    while True:
        try:
            print(f"[Connection] Connecting to {host}:{port} ...")
            sock = socket.create_connection((host, port), timeout=timeout)
            sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            print(f"[Connection] Connected to {host}:{port}")
            return sock
        except Exception as e:
            print(f"[Connection] Failed to connect to {host}:{port}: {e}")
            print(f"[Connection] Retrying in {reconnect_delay}s ...")
            time.sleep(reconnect_delay)


def safe_send(sock, payload: bytes, timeout: float = 5.0) -> bool:
    """
    Attempt to send payload on the socket.
    Returns:
      - True if send succeeded
      - False if socket appears blocked or broken
    """
    try:
        sock.settimeout(timeout)
        sock.sendall(payload)
        sock.settimeout(None)
        return True
    except Exception as e:
        print(f"[Connection] safe_send failed: {e}")
        return False
