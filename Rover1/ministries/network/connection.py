# Rover1/ministries/network/connection.py

import socket
import time


def configure_keepalive(sock: socket.socket):
    """Enable aggressive TCP keepalive."""
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
    sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPIDLE, 10)
    sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPINTVL, 5)
    sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPCNT, 3)


def safe_send(sock, data: bytes, max_block_ms=50):
    """
    Non-blocking send with soft timeout.
    Returns True if fully sent, False if blocked or failed.
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


def connect_with_retry(host, port, reconnect_delay=5):
    """
    Connect to host:port with retry loop.
    Returns a connected socket.
    """
    while True:
        try:
            print(f"[Connection] Connecting to {host}:{port}")
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            configure_keepalive(sock)
            sock.connect((host, port))
            print("[Connection] Connected")
            return sock

        except Exception as e:
            print(f"[Connection] Error: {e}, retrying in {reconnect_delay}s")
            time.sleep(reconnect_delay)
