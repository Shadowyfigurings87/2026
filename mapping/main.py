# /home/zachariah/2026/mapping/main.py

from multiprocessing import Process
from mapping.server.server_map import start_tile_server
from mapping.server.server_frontend import start_frontend_server

def start_mapping():
    print("[Mapping] Starting tile server (5000)…")
    p1 = Process(target=start_tile_server)
    p1.start()

    print("[Mapping] Starting frontend server (5001)…")
    p2 = Process(target=start_frontend_server)
    p2.start()

    return [p1, p2]
