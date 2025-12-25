# api/pages_routes.py

from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
import os

router = APIRouter(prefix="/dashboard")

TEMPLATES_DIR = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    "templates"
)

templates = Jinja2Templates(directory=TEMPLATES_DIR)


@router.get("/anomalies")
def anomalies_page(request: Request):
    return templates.TemplateResponse("anomalies.html", {"request": request})


@router.get("/devices")
def devices_page(request: Request):
    return templates.TemplateResponse("device_behavior.html", {"request": request})


@router.get("/channels")
def channels_page(request: Request):
    return templates.TemplateResponse("channel_health.html", {"request": request})


@router.get("/threat")
def threat_page(request: Request):
    return templates.TemplateResponse("threat_intel.html", {"request": request})

@router.get("/rover")
def rover_page(request: Request):
    return templates.TemplateResponse(
        "rover.html",
        {"request": request, "active_page": "rover"}
    )
@router.get("/camera/stream")
def rover_camera_stream():
    return StreamingResponse(
        open("/dev/shm/rover_cam.mjpeg", "rb"),
        media_type="multipart/x-mixed-replace; boundary=frame"
    )
@router.get("/camera/stream")
def rover_camera_stream():
    return RedirectResponse("http://redrover.local:81/stream")
