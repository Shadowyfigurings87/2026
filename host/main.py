# host/main.py

from host.logs.wrappers import log_api
import threading
import uvicorn


def start_ingestion():
    # TCP uplink ingestion server
    from host.services.ingest import start_ingestion_server
    start_ingestion_server()


def start_api():
    # FastAPI HTTP server
    uvicorn.run(
        "host.api.server:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        workers=1,
    )


def start_host():
    log_api("host_service_start")

    # Start ingestion in background
    ingestion_thread = threading.Thread(target=start_ingestion, daemon=True)
    ingestion_thread.start()

    # Start FastAPI (blocks)
    start_api()


def main():
    start_host()


if __name__ == "__main__":
    main()
