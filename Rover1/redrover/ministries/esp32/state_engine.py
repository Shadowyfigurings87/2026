import time
from dataclasses import dataclass, field
from typing import Dict, Optional


@dataclass
class BLEDeviceState:
    mac: str
    first_seen: float
    last_seen: float
    rssi: Optional[int] = None
    name: Optional[str] = None
    uuids: Optional[list] = None
    last_event_ts: float = field(default_factory=lambda: 0.0)


class BLEStateEngine:
    def __init__(self, event_cooldown=20.0, rssi_delta=5):
        self.devices: Dict[str, BLEDeviceState] = {}
        self.event_cooldown = event_cooldown
        self.rssi_delta = rssi_delta

    def _now(self):
        return time.time()

    def process(self, frame: dict) -> Optional[dict]:
        mac = frame.get("mac")
        if not mac:
            return None

        now = self._now()
        rssi = frame.get("rssi")
        name = frame.get("name")
        uuids = frame.get("uuids")

        state = self.devices.get(mac)

        # First time seen
        if state is None:
            state = BLEDeviceState(
                mac=mac,
                first_seen=now,
                last_seen=now,
                rssi=rssi,
                name=name,
                uuids=uuids,
                last_event_ts=now,
            )
            self.devices[mac] = state

            return {
                "event": "ble_device_seen",
                "ministry": "esp32",
                "kind": "ble_event",
                "mac": mac,
                "first_seen": now,
                "rssi": rssi,
                "name": name,
                "uuids": uuids,
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

        if name != state.name:
            changes["name"] = {"old": state.name, "new": name}
            state.name = name
            changed = True

        if uuids != state.uuids:
            changes["uuids"] = {"old": state.uuids, "new": uuids}
            state.uuids = uuids
            changed = True

        if not changed:
            return None

        if now - state.last_event_ts < self.event_cooldown:
            return None

        state.last_event_ts = now

        return {
            "event": "ble_device_updated",
            "ministry": "esp32",
            "kind": "ble_event",
            "mac": mac,
            "last_seen": now,
            "changes": changes,
            "rssi": state.rssi,
            "name": state.name,
            "uuids": state.uuids,
            "ts": frame.get("ts"),
        }
