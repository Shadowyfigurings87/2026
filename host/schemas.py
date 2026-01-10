# schemas.py

from pydantic import BaseModel
from typing import Optional, Any
from datetime import datetime

class TelemetryRecord(BaseModel):
    id: int
    timestamp_utc: Optional[str]
    ts: Optional[float]
    ministry: str
    payload: Any

class RFRecord(BaseModel):
    id: int
    timestamp_utc: Optional[str]
    rssi: Optional[int]
    subtype: Optional[str]
    payload: Any

class ArduinoState(BaseModel):
    timestamp_utc: Optional[str]
    state: Any

class HealthStatus(BaseModel):
    heartbeat_age_sec: float
    watchdog_age_sec: float
    last_heartbeat: Optional[str]
    last_watchdog: Optional[str]

class SystemStats(BaseModel):
    ingest_rate: float
    db_queue_depth: int
    uptime_sec: float
