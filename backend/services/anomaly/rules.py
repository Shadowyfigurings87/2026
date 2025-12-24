# services/anomaly/rules.py

from utils.logging_config import log_event
from utils.mac import lookup_vendor
import time
from collections import defaultdict, deque

# ---------------------------------------------------------------------------
# Stateful history for spoofing & jamming heuristics
# ---------------------------------------------------------------------------

# MAC -> deque of (timestamp, channel, rssi)
_mac_history = defaultdict(lambda: deque(maxlen=20))

# channel -> deque of (timestamp, channel_deviation, anomaly_score)
_channel_history = defaultdict(lambda: deque(maxlen=100))


# ---------------------------------------------------------------------------
# Stateless RULES (simple frame-level checks)
# ---------------------------------------------------------------------------

def rule_unknown_vendor(frame: dict):
    """
    Fires when the ML classifier did not assign a vendor.
    """
    vendor = frame.get("classification", {}).get("vendor")
    if vendor is None:
        return {
            "type": "unknown_vendor",
            "description": "Frame from unknown or unclassified vendor",
            "mac": frame.get("src_mac", "unknown"),
        }


def rule_very_strong_signal(frame: dict):
    """
    RSSI normalized above -20 dBm is suspiciously strong.
    """
    rssi_norm = frame.get("rssi_normalized")
    if rssi_norm is not None and rssi_norm > -20:
        return {
            "type": "very_strong_signal",
            "description": f"Unusually strong signal (rssi_normalized={rssi_norm})",
            "mac": frame.get("src_mac"),
        }


def rule_low_signal_quality(frame: dict):
    """
    Signal quality < 0.3 is suspicious.
    """
    sq = frame.get("signal_quality")
    if sq is not None and sq < 0.3:
        return {
            "type": "low_signal_quality",
            "description": f"Low signal quality (signal_quality={sq:.2f})",
            "mac": frame.get("src_mac"),
        }


def rule_management_storm(frame: dict):
    """
    High-volume management frame activity.
    """
    ft = frame.get("frame_type")
    activity = frame.get("activity_score")
    if ft == "management" and activity is not None and activity >= 3:
        return {
            "type": "management_storm",
            "description": "High-volume management frame activity",
            "mac": frame.get("src_mac"),
        }


# RULES list = stateless rules only
RULES = [
    rule_unknown_vendor,
    rule_very_strong_signal,
    rule_low_signal_quality,
    rule_management_storm,
]


# ---------------------------------------------------------------------------
# Helper: SSID prefix matching
# ---------------------------------------------------------------------------

def is_protected_ssid(ssid: str | None, prefixes: list[str]) -> bool:
    if not ssid:
        return False
    s = ssid.strip()
    return any(s.startswith(p) for p in prefixes)


# ---------------------------------------------------------------------------
# Heuristic Rule: Rogue AP Detection
# ---------------------------------------------------------------------------

def detect_rogue_ap(frame: dict, identity_map: dict, config: dict) -> list[dict]:
    """
    Heuristic:
      - BSSID not in identity_map / sensor inventory
      - BSSID vendor NOT in known_ap_vendors
      - SSID matches protected prefixes
    """
    alerts = []

    bssid = frame.get("bssid")
    ssid = frame.get("ssid")

    if not bssid or not ssid:
        return alerts

    known_vendors = config.get("known_ap_vendors", [])
    protected_prefixes = config.get("protected_ssid_prefixes", [])

    # If BSSID belongs to one of our sensors, ignore
    if (bssid or "").lower() in identity_map:
        return alerts

    vendor = lookup_vendor(bssid)
    vendor_ok = vendor and any(vendor.startswith(v) for v in known_vendors)

    if vendor_ok:
        return alerts

    if not is_protected_ssid(ssid, protected_prefixes):
        return alerts

    alerts.append({
        "type": "rogue_ap_suspected",
        "severity": "high",
        "mac": bssid,
        "description": f"Possible rogue AP: BSSID={bssid}, SSID={ssid}, vendor={vendor or 'unknown'}"
    })

    log_event("rules", "WARNING", "rogue_ap_suspected", {
        "bssid": bssid,
        "ssid": ssid,
        "vendor": vendor,
    })

    return alerts


# ---------------------------------------------------------------------------
# Heuristic Rule: Spoofing Detection
# ---------------------------------------------------------------------------

def detect_spoofing(frame: dict, identity_map: dict, config: dict) -> list[dict]:
    """
    Heuristic:
      - Same MAC seen on many channels in short time
      - Large RSSI variance in short time
    """
    alerts = []

    src_mac = frame.get("src_mac") or frame.get("src")
    if not src_mac:
        return alerts

    ch = frame.get("channel")
    rssi = frame.get("rssi_normalized") or frame.get("rssi")

    now = time.time()
    hist = _mac_history[src_mac]
    hist.append((now, ch, rssi))

    # Need some history
    if len(hist) < 3:
        return alerts

    # 30-second window
    recent = [h for h in hist if now - h[0] < 30]
    if len(recent) < 3:
        return alerts

    channels = {h[1] for h in recent if h[1] is not None}
    rssis = [h[2] for h in recent if h[2] is not None]

    # Multi-channel spoofing
    if len(channels) >= 3:
        alerts.append({
            "type": "mac_spoofing_suspected",
            "severity": "medium",
            "mac": src_mac,
            "description": f"MAC {src_mac} seen on {len(channels)} channels within 30s"
        })

    # RSSI variance spoofing
    if rssis and max(rssis) - min(rssis) > 35:
        alerts.append({
            "type": "mac_spoofing_suspected",
            "severity": "medium",
            "mac": src_mac,
            "description": f"MAC {src_mac} shows RSSI variance {max(rssis) - min(rssis):.1f} dB within 30s"
        })

    if alerts:
        log_event("rules", "WARNING", "spoofing_suspected", {
            "src_mac": src_mac,
            "channels": list(channels),
            "rssis": rssis,
        })

    return alerts


# ---------------------------------------------------------------------------
# Heuristic Rule: Jamming Detection
# ---------------------------------------------------------------------------

def detect_jamming(frame: dict, identity_map: dict, config: dict) -> list[dict]:
    """
    Heuristic:
      - High channel deviation
      - High anomaly score density
      - Within a short time window
    """
    alerts = []

    ch = frame.get("channel")
    if ch is None:
        return alerts

    ch_dev = frame.get("channel_deviation") or 0.0
    a_score = frame.get("anomaly_score") or 0.0
    now = time.time()

    hist = _channel_history[ch]
    hist.append((now, ch_dev, a_score))

    # 20-second window
    recent = [h for h in hist if now - h[0] < 20]
    if len(recent) < 10:
        return alerts

    avg_dev = sum(h[1] for h in recent) / len(recent)
    high_anomalies = [h for h in recent if h[2] > 0.7]

    if avg_dev > 0.6 and len(high_anomalies) > len(recent) * 0.4:
        alerts.append({
            "type": "jamming_suspected",
            "severity": "high",
            "mac": None,
            "description": (
                f"Possible jamming on channel {ch}: "
                f"avg_dev={avg_dev:.2f}, anomalies={len(high_anomalies)}/{len(recent)}"
            )
        })

        log_event("rules", "ALERT", "jamming_suspected", {
            "channel": ch,
            "avg_dev": avg_dev,
            "anomaly_count": len(high_anomalies),
            "window_size": len(recent),
        })

    return alerts
