from host.logs.wrappers import log_api
from host.services.ingest import start_ingestion_server
from host.services.db_writer import start_db_writer
import threading

def main():
    log_api("host_service_start")

    # Start DB writer in background
    threading.Thread(target=start_db_writer, daemon=True).start()

    # Run ingestion server in the main thread (BLOCKS FOREVER)
    start_ingestion_server()

if __name__ == "__main__":
    main()
