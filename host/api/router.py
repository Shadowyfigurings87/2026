# api/router.py

from fastapi import FastAPI
from api import telemetry, rf, arduino, health, system
from prometheus_client import make_asgi_app

metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)

def create_api():
    app = FastAPI(title="Rover1 Host API", version="1.0.0")

    app.include_router(telemetry.router, prefix="/telemetry", tags=["telemetry"])
    app.include_router(rf.router, prefix="/rf", tags=["rf"])
    app.include_router(arduino.router, prefix="/arduino", tags=["arduino"])
    app.include_router(health.router, prefix="/health", tags=["health"])
    app.include_router(system.router, prefix="/system", tags=["system"])

    return app

app = create_api()
