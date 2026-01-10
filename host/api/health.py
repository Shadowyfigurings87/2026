from fastapi import APIRouter
from services import db_reader
from services.metrics import heartbeat_age, watchdog_age
from schemas import HealthStatus

router = APIRouter()

@router.get("/summary", response_model=HealthStatus)
def get_health_summary():
    summary = db_reader.get_health_summary()

    # Update Prometheus metrics
    if summary["heartbeat_age_sec"] is not None:
        heartbeat_age.set(summary["heartbeat_age_sec"])
    if summary["watchdog_age_sec"] is not None:
        watchdog_age.set(summary["watchdog_age_sec"])

    return summary
