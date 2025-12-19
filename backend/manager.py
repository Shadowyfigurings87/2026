import threading
import uvicorn
from utils.logging import log_event

from ingest.shared_queue import ingest_queue
from ingest.tcp_ingest import start_tcp_ingest
from ingest.ingest_processor import start_ingest_processor
from db.writer import start_db_writer
from observatory.observatory import start_observatory, app as observatory_app
from api.server import app as api_app   # <-- import your existing API app

DB_PATH = "data/rf_archive.db"


def start_ministries():
    # TCP ingest ministry
    start_tcp_ingest(port=9000)

    # Ingest processor ministry
    start_ingest_processor(ingest_queue)

    # DB writer ministry
    start_db_writer(DB_PATH, ingest_queue)

    # Observatory ministry (heartbeat/logging)
    start_observatory()

    log_event("manager", "INFO", "ministries_online")


def start_observatory_api():
    # Run observatory FastAPI app
    uvicorn.run(
        observatory_app,
        host="0.0.0.0",
        port=8081,   # run observatory on 8081
        log_level="info"
    )


def start_main_api():
    # Run main API app
    uvicorn.run(
        api_app,
        host="0.0.0.0",
        port=8080,   # run main API on 8080
        log_level="info"
    )


if __name__ == "__main__":
    log_event("manager", "INFO", "manager_online")

    # Start ministries in background thread
    threading.Thread(target=start_ministries, daemon=True).start()

    # Start both APIs in parallel threads
    threading.Thread(target=start_observatory_api, daemon=True).start()
    threading.Thread(target=start_main_api, daemon=True).start()

    # Keep manager alive
    while True:
        pass
