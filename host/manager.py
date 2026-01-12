# host/main.py

from host.logs.wrappers import log_api

def start_host():
    log_api("host_service_start")

    try:
        from .api.server import start_server
        start_server()
    except ImportError:
        log_api("host_no_server_implementation")

if __name__ == "__main__":
    start_host()
