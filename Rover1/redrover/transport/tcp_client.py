import socket
import time


class TcpClient:
    """
    Persistent TCP client to Rover1.
    - Keeps a single connection open
    - Reconnects on failure
    - send(line) is safe to call from multiple threads
    """

    def __init__(self, host: str, port: int, reconnect_delay: float = 3.0):
        self.host = host
        self.port = port
        self.reconnect_delay = reconnect_delay
        self.sock = None

    def _connect(self):
        """Connect to Rover1, retrying until successful."""
        while True:
            try:
                s = socket.create_connection((self.host, self.port))
                s.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
                self.sock = s
                print(f"[tcp_client] connected to Rover1 at {self.host}:{self.port}", flush=True)
                return
            except Exception as e:
                print(f"[tcp_client] connect failed: {e}, retrying in {self.reconnect_delay}s", flush=True)
                time.sleep(self.reconnect_delay)

    def send(self, line: str):
        """
        Send a single JSONL line to Rover1.
        Auto-reconnects if the connection is lost.
        """
        if not line.endswith("\n"):
            line = line + "\n"

        if self.sock is None:
            self._connect()

        data = line.encode("utf-8")

        while True:
            try:
                self.sock.sendall(data)
                return
            except Exception as e:
                print(f"[tcp_client] send failed: {e}, reconnecting...", flush=True)
                try:
                    if self.sock is not None:
                        self.sock.close()
                except Exception:
                    pass
                self.sock = None
                self._connect()
