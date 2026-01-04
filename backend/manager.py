import threading
import uvicorn

from backend.utils.logging_config import log_event
from backend.services.shared_queue import ingest_queue
from backend.services.tcp_ingest import start_tcp_ingest
from backend.services.ingest_processor import start_ingest_processor
from backend.services.writer import start_db_writer
from backend.services.observatory import start_observatory

from backend.api.server import app as api_app


DB_PATH = "backend/data/rf_archive.db"


def start_ministries():
    """
    Launch all backend ministries:
      - TCP ingest (port 9000)
      - Ingest processor
      - DB writer
      - Observatory (heartbeat + metrics)
    """
    # TCP ingest ministry
    start_tcp_ingest(port=9000)

    # Ingest processor ministry
    start_ingest_processor(ingest_queue)

    # DB writer ministry
    start_db_writer(DB_PATH, ingest_queue)

    # Observatory background engine
    start_observatory()

    log_event("manager", "INFO", "ministries_online")


def start_main_api():
    """
    Launch the FastAPI server on port 8080 (or change to 6000 if desired).
    """
    uvicorn.run(
        api_app,
        host="0.0.0.0",
        port=8080,   # change to 6000 if you want
        log_level="info"
    )


if __name__ == "__main__":
    log_event("manager", "INFO", "manager_online")

    # Start ministries in background thread
    threading.Thread(target=start_ministries, daemon=True).start()

    # Start main API server in background thread
    threading.Thread(target=start_main_api, daemon=True).start()

    # Keep manager alive forever
    while True:
        pass
