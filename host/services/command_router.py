# host/services/command_router.py

import json

def send_command(sock, ministry, command, value=None):
    packet = {
        "ministry": ministry,
        "command": command,
        "value": value
    }
    line = json.dumps(packet) + "\n"
    sock.sendall(line.encode("utf-8"))
