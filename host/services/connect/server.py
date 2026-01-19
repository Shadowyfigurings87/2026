# host/services/connect/server.py
import socket
import threading

from host.logs.wrappers import log_ingest
from .worker import worker_loop
from .command_bus import command_forwarder_loop
from .dispatcher import dispatch_connection

HOST = "0.0.0.0"
PORT = 5000


def start_ingestion_server():
    """
    Start the ingestion server:
    - worker loop (ingestion_queue processor)
    - command forwarder (API -> rover)
    - TCP listener on port 5000
    """
    log_ingest("ingestion_server_start")

    # Start worker loop
    threading.Thread(target=worker_loop, daemon=True).start()

    # Start command forwarder
    threading.Thread(target=command_forwarder_loop, daemon=True).start()

    # Start TCP server
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind((HOST, PORT))
    sock.listen(5)

    log_ingest("ingestion_server_listening", host=HOST, port=PORT)

    while True:
        conn, addr = sock.accept()
        threading.Thread(
            target=dispatch_connection,
            args=(conn, addr),
            daemon=True,
        ).start()
