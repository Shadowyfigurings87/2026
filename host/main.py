# host/main.py

from host.api.server import start_server

def start_host():
    print("[Host] Starting ingestion server...")
    start_server()

if __name__ == "__main__":
    start_host()
