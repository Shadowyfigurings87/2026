# classifiers/device_classifier.py

from classifiers.vendor_lookup import lookup_vendor
from utils.mac import normalize_mac


def classify_frame(frame: dict) -> dict:
    """
    Given a frame row (dict), return a classification dict.
    Non-destructive: does not modify the original frame.
    """

    frame_type = frame.get("frame_type")
    subtype = frame.get("subtype")

    bssid = normalize_mac(frame.get("bssid"))
    src_mac = normalize_mac(frame.get("src_mac"))
    dst_mac = normalize_mac(frame.get("dst_mac"))

    vendor = lookup_vendor(bssid or src_mac)

    is_ap = False
    is_client = False
    device_role = "unknown"
    device_type = "unknown"

    # Basic role inference
    if frame_type == "management" and subtype in ("beacon", "probe_response"):
        is_ap = True
        device_role = "access_point"
        device_type = "AP"

    elif frame_type in ("management", "data") and subtype in ("probe_request", "data"):
        is_client = True
        device_role = "client"
        device_type = "STA"

    # Placeholder security flag
    security = "unknown"

    # Simple risk score heuristic
    risk_score = 0
    if vendor is None:
        risk_score += 10
    if bssid is None and is_ap:
        risk_score += 20

    # No anomaly score here (ingest assigns it)
    anomaly_score = None

    return {
        "vendor": vendor,
        "is_ap": is_ap,
        "is_client": is_client,
        "device_role": device_role,
        "device_type": device_type,
        "security": security,
        "risk_score": risk_score,
        "anomaly_score": anomaly_score,
        "normalized": {
            "bssid": bssid,
            "src_mac": src_mac,
            "dst_mac": dst_mac,
        },
    }
