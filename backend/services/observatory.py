import threading
import time
from collections import deque
from utils.logging_config import log_event
from prometheus_client import Gauge, Counter
import json

# -----------------------------
# Shared RF metrics
# -----------------------------
rf_metrics = {
    "total_frames": 0,
    "control_frames": 0,
    "management_frames": 0,
    "data_frames": 0,
    "rssi_values": [],
}

# Keep only the last 10 frames
recent_frames = deque(maxlen=10)

# -----------------------------
# Prometheus metrics
# -----------------------------
frames_total = Counter("frames_total", "Total frames observed")
frames_control = Counter("frames_control", "Control frames observed")
frames_management = Counter("frames_management", "Management frames observed")
frames_data = Counter("frames_data", "Data frames observed")

rssi_avg = Gauge("rssi_avg", "Average RSSI")
rssi_min = Gauge("rssi_min", "Minimum RSSI")
rssi_max = Gauge("rssi_max", "Maximum RSSI")

anomaly_score_metric = Gauge("anomaly_score", "Latest anomaly score")

recent_frame_info = Gauge(
    "recent_frame_info",
    "Recent frame details",
    ["timestamp", "src", "dst", "frame_type", "subtype", "rssi", "signal_quality"]
)

# -----------------------------
# Update functions
# -----------------------------
def update_metrics(frame):
    """Called by ingest_processor when a frame is processed."""
    rf_metrics["total_frames"] += 1
    frames_total.inc()

    ftype = frame.get("frame_type")
    if ftype == "control":
        rf_metrics["control_frames"] += 1
        frames_control.inc()
    elif ftype == "management":
        rf_metrics["management_frames"] += 1
        frames_management.inc()
    elif ftype == "data":
        rf_metrics["data_frames"] += 1
        frames_data.inc()

    # RSSI tracking
    rssi = frame.get("rssi")
    if rssi is not None:
        rf_metrics["rssi_values"].append(rssi)

    # Keep recent frames
    recent_frames.append(frame)

    # Update Prometheus recent_frame_info
    recent_frame_info.clear()
    for f in list(recent_frames):
        recent_frame_info.labels(
            timestamp=str(f.get("timestamp")),
            src=str(f.get("src")),
            dst=str(f.get("dst")),
            frame_type=str(f.get("frame_type")),
            subtype=str(f.get("subtype")),
            rssi=str(f.get("rssi")),
            signal_quality=str(f.get("signal_quality")),
        ).set(1)

def update_anomaly_score(score, frame_type):
    """Called when anomaly engine produces a score."""
    anomaly_score_metric.set(score)
    log_event("observatory", "INFO", "anomaly_score_update", {
        "score": score,
        "frame_type": frame_type
    })

# -----------------------------
# Dashboard data helper
# -----------------------------
def get_dashboard_data():
    """Returns a dict used by the dashboard template."""
    if rf_metrics["rssi_values"]:
        avg_rssi = sum(rf_metrics["rssi_values"]) / len(rf_metrics["rssi_values"])
        min_rssi = min(rf_metrics["rssi_values"])
        max_rssi = max(rf_metrics["rssi_values"])
    else:
        avg_rssi = min_rssi = max_rssi = None

    return {
        "total": rf_metrics["total_frames"],
        "control": rf_metrics["control_frames"],
        "management": rf_metrics["management_frames"],
        "data": rf_metrics["data_frames"],
        "avg_rssi": avg_rssi,
        "min_rssi": min_rssi,
        "max_rssi": max_rssi,
        "recent_frames": list(recent_frames),
    }

# -----------------------------
# Observatory heartbeat
# -----------------------------
def run_observatory():
    log_event("observatory", "INFO", "observatory_online")

    while True:
        time.sleep(10)

        if rf_metrics["rssi_values"]:
            avg_rssi = sum(rf_metrics["rssi_values"]) / len(rf_metrics["rssi_values"])
            min_rssi = min(rf_metrics["rssi_values"])
            max_rssi = max(rf_metrics["rssi_values"])
        else:
            avg_rssi = min_rssi = max_rssi = None

        # Update Prometheus gauges
        if avg_rssi is not None:
            rssi_avg.set(avg_rssi)
            rssi_min.set(min_rssi)
            rssi_max.set(max_rssi)

        # Log metrics heartbeat
        log_event("observatory", "INFO", "rf_metrics_update", {
            "total": rf_metrics["total_frames"],
            "control": rf_metrics["control_frames"],
            "management": rf_metrics["management_frames"],
            "data": rf_metrics["data_frames"],
            "avg_rssi": avg_rssi,
            "min_rssi": min_rssi,
            "max_rssi": max_rssi,
        })

        # Log recent frames
        for f in list(recent_frames):
            log_event("observatory", "DEBUG", "recent_frame", {
                "timestamp": f.get("timestamp"),
                "src": f.get("src"),
                "dst": f.get("dst"),
                "frame_type": f.get("frame_type"),
                "subtype": f.get("subtype"),
                "rssi": f.get("rssi"),
                "signal_quality": f.get("signal_quality"),
            })

def start_observatory():
    t = threading.Thread(target=run_observatory, daemon=True)
    t.start()

# services/observatory.py (additions sketch)

# ---------------------------------------------------------------------------
# WebSocket: Live anomaly events
# ---------------------------------------------------------------------------

import json

_live_anomaly_clients = set()

def register_anomaly_ws(ws):
    _live_anomaly_clients.add(ws)

def unregister_anomaly_ws(ws):
    _live_anomaly_clients.discard(ws)

def broadcast_anomaly_event(event: dict):
    dead = []
    msg = json.dumps(event)
    for ws in list(_live_anomaly_clients):
        try:
            ws.send(msg)
        except Exception:
            dead.append(ws)
    for ws in dead:
        _live_anomaly_clients.discard(ws)


# ---------------------------------------------------------------------------
# WebSocket: Rule-based alert events
# ---------------------------------------------------------------------------

_live_rule_clients = set()

def register_rule_ws(ws):
    _live_rule_clients.add(ws)

def unregister_rule_ws(ws):
    _live_rule_clients.discard(ws)

def broadcast_rule_alert(alert: dict):
    dead = []
    msg = json.dumps(alert)
    for ws in list(_live_rule_clients):
        try:
            ws.send(msg)
        except Exception:
            dead.append(ws)
    for ws in dead:
        _live_rule_clients.discard(ws)
