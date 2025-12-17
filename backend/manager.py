import threading
import queue
import uvicorn

from ingest.ingest_stdin import start_stdin_ingest
from ingest.ingest_processor import start_ingest_processor
from db.writer import start_db_writer
from server.app import app
from utils.config import load_config


def start_api_server(config):
    uvicorn.run(
        app,
        host=config["server"]["host"],
        port=config["server"]["port"],
        reload=False,
        workers=1
    )


def main():
    config = load_config()

    ingest_queue = queue.Queue(maxsize=5000)

    start_db_writer()
    start_stdin_ingest(ingest_queue)
    start_ingest_processor(ingest_queue)

    api_thread = threading.Thread(
        target=start_api_server,
        args=(config,),
        daemon=True
    )
    api_thread.start()

    api_thread.join()


if __name__ == "__main__":
    main()
