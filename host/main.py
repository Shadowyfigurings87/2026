# host/main.py

from host.logs.wrappers import log_system
from host.services.connect.server import start_ingestion_server
from host.services.db_writer import start_db_writer
import threading
import uvicorn

def start_api():
    """
    Launch FastAPI on port 8000 using your router.py app.
    """
    from host.api.router import app

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=False,
        workers=1,
    )

def main():
    log_system("host_service_start")

    # Start DB writer
    threading.Thread(target=start_db_writer, daemon=True).start()

    # Start FastAPI server in background
    threading.Thread(target=start_api, daemon=True).start()

    # Start ingestion server in main thread (blocks forever)
    start_ingestion_server()

if __name__ == "__main__":
    main()
