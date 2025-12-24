# api/sensors_routes.py

from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
import os

router = APIRouter(prefix="/dashboard")   # <-- IMPORTANT

TEMPLATES_DIR = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    "templates"
)

templates = Jinja2Templates(directory=TEMPLATES_DIR)

@router.get("/sensors")
def sensors_page(request: Request):
    # Placeholder data — replace with real sensor logic later
    sensors = [
        {"name": "Sensor A", "online": True, "last_heartbeat": "2025-12-22 04:30", "avg_rssi": -55},
        {"name": "Sensor B", "online": False, "last_heartbeat": "2025-12-22 04:10", "avg_rssi": -70},
    ]

    labels = ["00:00", "00:05", "00:10", "00:15"]
    rssi = [-55, -57, -54, -56]

    return templates.TemplateResponse(
        "system.html",
        {
            "request": request,
            "sensors": sensors,
            "labels": labels,
            "rssi": rssi
        }
    )
