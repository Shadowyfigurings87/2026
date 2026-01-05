# host/main.py

def start_host():
    print("Starting host service...")
    # Import lazily so your modules load only when needed
    try:
        from .api.server import run_server
        run_server()
    except ImportError:
        print("No server implementation yet. Add your logic in host/api/server.py")

if __name__ == "__main__":
    start_host()
