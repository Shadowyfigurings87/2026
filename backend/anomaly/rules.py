# anomaly/rules.py

def rule_unknown_vendor(frame: dict):
    vendor = frame.get("classification", {}).get("vendor")
    if vendor is None:
        return {
            "type": "unknown_vendor",
            "description": "Frame from unknown or unclassified vendor",
            "mac": frame.get("src_mac", "unkown"),
        }


def rule_very_strong_signal(frame: dict):
    rssi_norm = frame.get("rssi_normalized")
    if rssi_norm is not None and rssi_norm > -20:
        return {
            "type": "very_strong_signal",
            "description": f"Unusually strong signal (rssi_normalized={rssi_norm})",
            "mac": frame.get("src_mac"),
        }


def rule_low_signal_quality(frame: dict):
    sq = frame.get("signal_quality")
    if sq is not None and sq < 0.3:
        return {
            "type": "low_signal_quality",
            "description": f"Low signal quality (signal_quality={sq:.2f})",
            "mac": frame.get("src_mac"),
        }


def rule_management_storm(frame: dict):
    """
    Example: if activity_score is high and frame_type is management,
    we treat it as a possible management frame storm.
    """
    ft = frame.get("frame_type")
    activity = frame.get("activity_score")
    if ft == "management" and activity is not None and activity >= 3:
        return {
            "type": "management_storm",
            "description": "High-volume management frame activity",
            "mac": frame.get("src_mac"),
        }


RULES = [
    rule_unknown_vendor,
    rule_very_strong_signal,
    rule_low_signal_quality,
    rule_management_storm,
]
