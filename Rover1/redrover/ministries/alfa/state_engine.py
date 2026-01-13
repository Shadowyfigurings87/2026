# redrover/ministries/alfa/state_engine.py

import time
from dataclasses import dataclass, field
from typing import Dict, Optional


@dataclass
class DeviceState:
    mac: str
    first_seen: float
    last_seen: float
    rssi: Optional[int] = None
    ssid: Optional[str] = None
    channel: Optional[int] = None
    security: Optional[str] = None
    last_event_ts: float = field(default_factory=lambda: 0.0)


@dataclass
class APState:
    bssid: str
    first_seen: float
    last_seen: float
    ssid: Optional[str] = None
    channel: Optional[int] = None
    security: Optional[str] = None
    last_event_ts: float = field(default_factory=lambda: 0.0)


class RFStateEngine:
    def __init__(
        self,
        event_cooldown: float = 30.0,
        rssi_delta: int = 5,
    ):
        self.devices: Dict[str, DeviceState] = {}
        self.aps: Dict[str, APState] = {}
        self.event_cooldown = event_cooldown
        self.rssi_delta = rssi_delta

    def _now(self) -> float:
        return time.time()

    def _should_emit(self, last_ts: float) -> bool:
        return (self._now() - last_ts) >= self.event_cooldown

    def _update_device(self, frame: dict) -> Optional[dict]:
        mac = frame.get("src") or frame.get("bssid") or frame.get("dst")
        if not mac:
            return None

        now = self._now()
        rssi = frame.get("rssi")
        ssid = frame.get("ssid")
        channel = frame.get("channel")
        security = frame.get("security")

        state = self.devices.get(mac)

        # First time seen
        if state is None:
            state = DeviceState(
                mac=mac,
                first_seen=now,
                last_seen=now,
                rssi=rssi,
                ssid=ssid,
                channel=channel,
                security=security,
                last_event_ts=now,
            )
            self.devices[mac] = state

            return {
                "event": "device_seen",
                "ministry": "alfa",
                "kind": "rf_event",
                "mac": mac,
                "first_seen": now,
                "rssi": rssi,
                "ssid": ssid,
                "channel": channel,
                "security": security,
                "frame_type": frame.get("frame_type"),
                "src": frame.get("src"),
                "dst": frame.get("dst"),
                "bssid": frame.get("bssid"),
                "ts": frame.get("ts"),
            }

        # Existing device
        state.last_seen = now
        changes = {}
        changed = False

        if rssi is not None and state.rssi is not None:
            if abs(rssi - state.rssi) >= self.rssi_delta:
                changes["rssi"] = {"old": state.rssi, "new": rssi}
                state.rssi = rssi
                changed = True
        elif rssi is not None and state.rssi is None:
            changes["rssi"] = {"old": None, "new": rssi}
            state.rssi = rssi
            changed = True

        if ssid != state.ssid:
            changes["ssid"] = {"old": state.ssid, "new": ssid}
            state.ssid = ssid
            changed = True

        if channel != state.channel:
            changes["channel"] = {"old": state.channel, "new": channel}
            state.channel = channel
            changed = True

        if security != state.security:
            changes["security"] = {"old": state.security, "new": security}
            state.security = security
            changed = True

        if not changed:
            return None

        if not self._should_emit(state.last_event_ts):
            return None

        state.last_event_ts = now

        return {
            "event": "device_updated",
            "ministry": "alfa",
            "kind": "rf_event",
            "mac": mac,
            "last_seen": now,
            "changes": changes,
            "rssi": state.rssi,
            "ssid": state.ssid,
            "channel": state.channel,
            "security": state.security,
            "frame_type": frame.get("frame_type"),
            "src": frame.get("src"),
            "dst": frame.get("dst"),
            "bssid": frame.get("bssid"),
            "ts": frame.get("ts"),
        }

    def _update_ap(self, frame: dict) -> Optional[dict]:
        bssid = frame.get("bssid")
        if not bssid:
            return None

        now = self._now()
        ssid = frame.get("ssid")
        channel = frame.get("channel")
        security = frame.get("security")

        state = self.aps.get(bssid)

        # First time AP seen
        if state is None:
            state = APState(
                bssid=bssid,
                first_seen=now,
                last_seen=now,
                ssid=ssid,
                channel=channel,
                security=security,
                last_event_ts=now,
            )
            self.aps[bssid] = state

            return {
                "event": "ap_seen",
                "ministry": "alfa",
                "kind": "rf_event",
                "bssid": bssid,
                "first_seen": now,
                "ssid": ssid,
                "channel": channel,
                "security": security,
                "ts": frame.get("ts"),
            }

        # Existing AP
        state.last_seen = now
        changes = {}
        changed = False

        if ssid != state.ssid:
            changes["ssid"] = {"old": state.ssid, "new": ssid}
            state.ssid = ssid
            changed = True

        if channel != state.channel:
            changes["channel"] = {"old": state.channel, "new": channel}
            state.channel = channel
            changed = True

        if security != state.security:
            changes["security"] = {"old": state.security, "new": security}
            state.security = security
            changed = True

        if not changed:
            return None

        if not self._should_emit(state.last_event_ts):
            return None

        state.last_event_ts = now

        return {
            "event": "ap_updated",
            "ministry": "alfa",
            "kind": "rf_event",
            "bssid": bssid,
            "last_seen": now,
            "changes": changes,
            "ssid": state.ssid,
            "channel": state.channel,
            "security": state.security,
            "ts": frame.get("ts"),
        }

    def process_frame(self, frame: dict) -> Optional[dict]:
        """
        Entry point: given a parsed wifi_frame, decide what RF event to emit.
        Priority:
          - AP events for beacon/probe frames
          - Device events for everything else
        """
        frame_type = frame.get("frame_type", "")

        # Beacon / probe → AP-centric events
        if frame_type.startswith("0/8") or frame_type.startswith("0/4"):
            ap_event = self._update_ap(frame)
            if ap_event:
                return ap_event

        # Device-centric events
        return self._update_device(frame)
