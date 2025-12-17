from pydantic import BaseModel
from typing import Optional, Dict, Any


# ---------------------------------------------------------
# Classification Schema
# ---------------------------------------------------------

class FrameClassification(BaseModel):
    vendor: Optional[str] = None
    is_ap: bool
    is_client: bool
    device_role: Optional[str] = None
    device_type: Optional[str] = None  # AP, STA, unknown
    security: Optional[str] = None
    risk_score: Optional[int] = None
    anomaly_score: Optional[float] = None
    confidence: Optional[float] = None  # future ML
    normalized: Optional[Dict[str, Any]] = None


# ---------------------------------------------------------
# Frame Schema
# ---------------------------------------------------------

class FrameOut(BaseModel):
    id: int
    timestamp: str

    # Core frame metadata
    source: Optional[str] = None
    iface: Optional[str] = None
    frame_type: str
    subtype: Optional[str] = None
    direction: Optional[str] = None

    # MAC addresses
    src_mac: Optional[str] = None
    dst_mac: Optional[str] = None
    bssid: Optional[str] = None

    # RF metadata
    channel: Optional[int] = None
    channel_freq: Optional[int] = None
    channel_flags: Optional[str] = None
    rssi: Optional[int] = None
    rssi_normalized: Optional[int] = None
    signal_quality: Optional[float] = None
    activity_score: Optional[float] = None
    rate: Optional[int] = None

    # Sensor attribution
    sensor_id: Optional[int] = None
    sensor_component_role: Optional[str] = None

    # Summary + classification
    summary: Optional[str] = None
    classification: Optional[FrameClassification] = None


# ---------------------------------------------------------
# Alerts
# ---------------------------------------------------------

class AlertOut(BaseModel):
    id: int
    timestamp: str
    alert_type: str
    mac: Optional[str] = None
    sensor_id: Optional[int] = None
    component_role: Optional[str] = None
    severity: Optional[float] = None
    description: Optional[str] = None


# ---------------------------------------------------------
# Channel Metrics
# ---------------------------------------------------------

class ChannelMetricOut(BaseModel):
    id: int
    timestamp: str
    channel: int
    sensor_id: Optional[int] = None
    component_role: Optional[str] = None
    activity_score: Optional[float] = None


# ---------------------------------------------------------
# Sensor Status
# ---------------------------------------------------------

class SensorStatusOut(BaseModel):
    id: int
    sensor_id: int
    last_seen: str
    component_mac: Optional[str] = None
    component_role: Optional[str] = None


# ---------------------------------------------------------
# System Health
# ---------------------------------------------------------

class SystemHealthOut(BaseModel):
    frames: int
    alerts: int
    registered_sensors: int
