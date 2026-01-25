# host/services/connect/dispatcher.py

import socket
from host.logs.wrappers import log_ingest
from .json_handler import handle_json_client


def dispatch_connection(conn, addr):
    """
    Rover1-compatible dispatcher.
    Accepts the connection and immediately hands it to the JSON handler.
    No peeking, no protocol detection, no routing logic.
    Rover1 sends line-delimited JSON and expects a raw TCP ingestion server.
    """
    try:
        log_ingest("json_connection_detected", addr=str(addr))
        handle_json_client(conn, addr)

    except Exception as e:
        log_ingest("dispatcher_crashed", error=str(e), addr=str(addr))
        try:
            conn.close()
        except Exception:
            pass
