from host.logs.logging import info
# host/main.py

import threading
import uvicorn

def start_ingestion():
    from host.api.server import start_server
    start_server()

def start_api():
    uvicorn.run(
        "host.api.router:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        workers=1,
    )

def start_host():
    info("Starting unified Rover Host service…")

    # Start ingestion in a background thread
    ingestion_thread = threading.Thread(target=start_ingestion, daemon=True)
    ingestion_thread.start()

    # Start FastAPI (this blocks)
    start_api()

def main():
    start_host()

if __name__ == "__main__":
    main()
