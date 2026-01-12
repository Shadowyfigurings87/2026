# host/services/command_router.py

from host.logs.wrappers import log_ingest
import json

def send_command(sock, ministry, command, value=None):
    packet = {
        "ministry": ministry,
        "command": command,
        "value": value
    }

    try:
        line = json.dumps(packet) + "\n"
        sock.sendall(line.encode("utf-8"))
        log_ingest("ingest_command_sent", ministry=ministry, command=command, value=value)
    except Exception as e:
        log_ingest("ingest_command_error", ministry=ministry, command=command, error=str(e))
