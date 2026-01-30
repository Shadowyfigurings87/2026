from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from prometheus_client import make_asgi_app
from host.api.camera import router as camera_router

import os

# MJPEG route registration
from host.services.camera.mjpeg_router import register_routes

# Routers
from host.api.telemetry import router as telemetry_router
from host.api.rf import router as rf_router
from host.api.arduino import router as arduino_router
from host.api.health import router as health_router
from host.api.system import router as system_router
from host.api.dashboard import router as dashboard_router
from host.api.esp32 import router as esp32_router
from host.services.command_pipeline.command_api_v2 import router as command_v2_router
from host.api.routes_gps import router as gps_router   # ⭐ FIXED

def create_api():
    app = FastAPI(title="Rover1 Host API", version="1.0.0")

    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    STATIC_DIR = os.path.join(BASE_DIR, "static")
    TEMPLATE_DIR = os.path.join(BASE_DIR, "templates")

    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
    templates = Jinja2Templates(directory=TEMPLATE_DIR)

    # ---------------------------------------------------------
    # MINISTRY ROUTERS
    # ---------------------------------------------------------
    app.include_router(telemetry_router)
    app.include_router(rf_router, prefix="/rf", tags=["rf"])
    app.include_router(arduino_router, prefix="/arduino", tags=["arduino"])
    app.include_router(health_router, prefix="/health", tags=["health"])
    app.include_router(system_router, prefix="/system", tags=["system"])
    app.include_router(dashboard_router, prefix="/dashboard", tags=["dashboard"])
    app.include_router(esp32_router, prefix="/esp32", tags=["esp32"])
    app.include_router(command_v2_router)

    # ⭐ NEW GPS ROUTER
    app.include_router(gps_router, prefix="/gps", tags=["gps"])

    # ---------------------------------------------------------
    # CAMERA MJPEG ENDPOINT
    # ---------------------------------------------------------
    register_routes(app)
    app.include_router(camera_router, prefix="/camera")

    # ---------------------------------------------------------
    # PROMETHEUS METRICS
    # ---------------------------------------------------------
    metrics_app = make_asgi_app()
    app.mount("/metrics", metrics_app)

    return app

app = create_api()
