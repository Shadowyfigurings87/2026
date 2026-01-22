# host/services/connect/dispatcher.py

import socket

from host.logs.wrappers import log_ingest

from .json_handler import handle_json_client
# MJPEG handler removed — no longer used
# from .mjpeg_handler import handle_mjpeg_client


def dispatch_connection(conn, addr):
    """
    Peek at the first bytes and route to JSON handler only.
    MJPEG routing has been removed.
    """
    try:
        first = conn.recv(64, socket.MSG_PEEK)
        if not first:
            log_ingest("ingest_empty_connection", addr=str(addr))
            conn.close()
            return

        stripped = first.lstrip()

        # JSON
        if stripped.startswith(b"{"):
            log_ingest("json_connection_detected", addr=str(addr))
            handle_json_client(conn, addr)
            return

        # Fallback to JSON
        log_ingest("fallback_to_json_handler", addr=str(addr))
        handle_json_client(conn, addr)

    except Exception as e:
        log_ingest("dispatcher_crashed", error=str(e), addr=str(addr))
        try:
            conn.close()
        except Exception:
            pass
