import threading
import time
from utils.logging_config import log_event

# Shared RF metrics state
rf_metrics = {
    "total_frames": 0,
    "management_frames": 0,
    "control_frames": 0,
    "data_frames": 0,
    "last_update": None,
}

def update_metrics(frame):
    """
    Called by ingest_processor to update observatory metrics.
    """
    rf_metrics["total_frames"] += 1

    ftype = frame.get("frame_type")
    if ftype == "management":
        rf_metrics["management_frames"] += 1
    elif ftype == "control":
        rf_metrics["control_frames"] += 1
    elif ftype == "data":
        rf_metrics["data_frames"] += 1

    rf_metrics["last_update"] = frame.get("timestamp")


def run_observatory():
    """
    Background thread that periodically emits RF metrics.
    """
    log_event("observatory", "INFO", "observatory_online")

    while True:
        time.sleep(10)

        log_event("observatory", "INFO", "rf_metrics_update", {
            "total": rf_metrics["total_frames"],
            "management": rf_metrics["management_frames"],
            "control": rf_metrics["control_frames"],
            "data": rf_metrics["data_frames"],
            "last_update": rf_metrics["last_update"],
        })


def start_observatory():
    """
    Launch the observatory ministry.
    """
    t = threading.Thread(target=run_observatory, daemon=True)
    t.start()
