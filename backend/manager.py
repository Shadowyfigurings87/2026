import threading
from utils.logging_config import log_event
from services.shared_queue import ingest_queue
from services.tcp_ingest import start_tcp_ingest
from services.ingest_processor import start_ingest_processor
from services.writer import start_db_writer
from services.observatory import start_observatory
import uvicorn
from api.server import app as api_app

DB_PATH = "data/rf_archive.db"


def start_ministries():
    # TCP ingest ministry
    start_tcp_ingest(port=9000)

    # Ingest processor ministry
    start_ingest_processor(ingest_queue)

    # DB writer ministry
    start_db_writer(DB_PATH, ingest_queue)

    # Observatory background engine (heartbeat + metrics)
    start_observatory()

    log_event("manager", "INFO", "ministries_online")


def start_main_api():
    uvicorn.run(
        api_app,
        host="0.0.0.0",
        port=8080,
        log_level="info"
    )


if __name__ == "__main__":
    log_event("manager", "INFO", "manager_online")

    # Start ministries in background thread
    threading.Thread(target=start_ministries, daemon=True).start()

    # Start main API server
    threading.Thread(target=start_main_api, daemon=True).start()

    # Keep manager alive
    while True:
        pass
