# host/api/router.py

from fastapi import FastAPI
from prometheus_client import make_asgi_app

# Import all routers
from host.api.telemetry import router as telemetry_router
from host.api.rf import router as rf_router
from host.api.arduino import router as arduino_router
from host.api.health import router as health_router
from host.api.system import router as system_router
from host.api.dashboard import router as dashboard_router
from host.api.camera import router as camera_router
from host.api.command_api import router as command_router
from host.api.esp32 import router as esp32_router


def create_api():
    app = FastAPI(title="Rover1 Host API", version="1.0.0")

    # Include all ministry routers
    app.include_router(telemetry_router, prefix="/telemetry", tags=["telemetry"])
    app.include_router(rf_router, prefix="/rf", tags=["rf"])
    app.include_router(arduino_router, prefix="/arduino", tags=["arduino"])
    app.include_router(health_router, prefix="/health", tags=["health"])
    app.include_router(system_router, prefix="/system", tags=["system"])
    app.include_router(dashboard_router, prefix="/dashboard", tags=["dashboard"])
    app.include_router(camera_router, prefix="/camera", tags=["camera"])
    app.include_router(command_router, prefix="/command", tags=["command"])
    app.include_router(esp32_router, prefix="/arduino", tags=["esp32"])

    # Prometheus metrics
    metrics_app = make_asgi_app()
    app.mount("/metrics", metrics_app)

    return app


app = create_api()
