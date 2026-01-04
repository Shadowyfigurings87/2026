from fastapi import APIRouter
from backend.services.shared_queue import ingest_queue

router = APIRouter(prefix="/dashboard")

@router.get("/ingest/status")
def ingest_status():
    return {
        "queue_size": ingest_queue.qsize(),
        "status": "running"
    }
