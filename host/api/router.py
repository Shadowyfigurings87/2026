from fastapi import FastAPI
from host.api import telemetry, rf, arduino, health, system
from prometheus_client import make_asgi_app
from . import dashboard

def create_api():
    app = FastAPI(title="Rover1 Host API", version="1.0.0")

    # Include all ministry routers
    app.include_router(telemetry.router, prefix="/telemetry", tags=["telemetry"])
    app.include_router(rf.router, prefix="/rf", tags=["rf"])
    app.include_router(arduino.router, prefix="/arduino", tags=["arduino"])
    app.include_router(health.router, prefix="/health", tags=["health"])
    app.include_router(system.router, prefix="/system", tags=["system"])
    app.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])

    # Mount Prometheus metrics
    metrics_app = make_asgi_app()
    app.mount("/metrics", metrics_app)

    return app

app = create_api()
