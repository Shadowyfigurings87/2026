# host/services/connect/command_bus.py

import json
import threading
from queue import Queue, Empty
from host.logs.wrappers import log_ingest

# Queue of JSON command dicts
command_queue: Queue = Queue()

# Rover uplink socket
_rover_socket = None
_rover_lock = threading.Lock()


def set_rover_socket(sock):
    """
    Register or update the rover control/telemetry socket.
    """
    global _rover_socket
    with _rover_lock:
        _rover_socket = sock
        log_ingest("rover_socket_registered")


def clear_rover_socket():
    global _rover_socket
    with _rover_lock:
        _rover_socket = None
        log_ingest("rover_socket_cleared")


def get_rover_socket():
    with _rover_lock:
        return _rover_socket


def enqueue_command(cmd_obj: dict):
    """
    Accept a JSON command dict and enqueue it for sending.
    """
    try:
        payload = json.dumps(cmd_obj).encode("utf-8") + b"\n"
        command_queue.put(payload)
        log_ingest("command_enqueued", payload=cmd_obj)
    except Exception as e:
        log_ingest("command_enqueue_error", error=str(e), payload=cmd_obj)


def command_forwarder_loop():
    """
    Background loop that forwards JSON commands to the rover uplink socket.
    """
    log_ingest("command_forwarder_started")

    while True:
        try:
            cmd_bytes = command_queue.get(timeout=1.0)
        except Empty:
            continue

        sock = get_rover_socket()
        if sock is None:
            log_ingest("command_dropped_no_rover_socket")
            command_queue.task_done()
            continue

        try:
            sock.sendall(cmd_bytes)
            log_ingest("command_sent_to_rover", size=len(cmd_bytes))
        except Exception as e:
            log_ingest("command_send_error", error=str(e))
            clear_rover_socket()
        finally:
            command_queue.task_done()
