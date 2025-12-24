# api/observatory_routes.py

from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
import os

router = APIRouter(prefix="/dashboard")

TEMPLATES_DIR = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    "templates"
)

templates = Jinja2Templates(directory=TEMPLATES_DIR)


@router.get("/observatory")
def observatory_page(request: Request):
    return templates.TemplateResponse("observatory.html", {"request": request})


@router.get("/devices")
def device_behavior_page(request: Request):
    return templates.TemplateResponse("device_behavior.html", {"request": request})


@router.get("/channels")
def channel_health_page(request: Request):
    return templates.TemplateResponse("channel_health.html", {"request": request})


@router.get("/anomalies")
def anomalies_page(request: Request):
    return templates.TemplateResponse("anomalies.html", {"request": request})


@router.get("/threat")
def threat_page(request: Request):
    return templates.TemplateResponse("threat_intel.html", {"request": request})
