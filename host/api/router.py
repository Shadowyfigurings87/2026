from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from prometheus_client import make_asgi_app

# MJPEG route registration
from host.services.camera.mjpeg_router import register_routes

# Routers
from host.api.telemetry import router as telemetry_router
from host.api.rf import router as rf_router
from host.api.arduino import router as arduino_router
from host.api.health import router as health_router
from host.api.system import router as system_router
from host.api.dashboard import router as dashboard_router
from host.api.command_api import router as command_router
from host.api.esp32 import router as esp32_router


def create_api():
    app = FastAPI(title="Rover1 Host API", version="1.0.0")

    # ---------------------------------------------------------
    # STATIC + TEMPLATE MOUNTS
    # ---------------------------------------------------------
    app.mount("/static", StaticFiles(directory="host/static"), name="static")
    templates = Jinja2Templates(directory="host/templates")

    # ---------------------------------------------------------
    # MINISTRY ROUTERS
    # ---------------------------------------------------------
    app.include_router(telemetry_router)
    app.include_router(rf_router, prefix="/rf", tags=["rf"])
    app.include_router(arduino_router, prefix="/arduino", tags=["arduino"])
    app.include_router(health_router, prefix="/health", tags=["health"])
    app.include_router(system_router, prefix="/system", tags=["system"])
    app.include_router(dashboard_router, prefix="/dashboard", tags=["dashboard"])
    app.include_router(command_router, prefix="/command", tags=["command"])
    app.include_router(esp32_router, prefix="/esp32", tags=["esp32"])

    # ---------------------------------------------------------
    # CAMERA MJPEG ENDPOINT
    # ---------------------------------------------------------
    register_routes(app)

    # ---------------------------------------------------------
    # PROMETHEUS METRICS
    # ---------------------------------------------------------
    metrics_app = make_asgi_app()
    app.mount("/metrics", metrics_app)

    return app


app = create_api()
