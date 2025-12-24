from fastapi import FastAPI
from fastapi.responses import Response
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

# Import FastAPI routers (NOT Flask blueprints)
from api.observatory_routes import router as observatory_router
from api.ingest_routes import router as ingest_router
from api.system_routes import router as system_router
from api.sensors_routes import router as sensors_router
from api.anomaly_routes import router as anomaly_router
from api.frame_routes import router as frame_router
from api.device_routes import router as device_router
from api.channel_routes import router as channel_router
from api.threat_routes import router as threat_router
from api.pages_routes import router as pages_router

app = FastAPI()

# Register routers (each exactly once)
app.include_router(observatory_router)
app.include_router(ingest_router)
app.include_router(system_router)
app.include_router(sensors_router)
app.include_router(anomaly_router)
app.include_router(frame_router)
app.include_router(device_router)
app.include_router(channel_router)
app.include_router(threat_router)
app.include_router(pages_router)

# Prometheus metrics endpoint
@app.get("/metrics")
def prometheus_metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
