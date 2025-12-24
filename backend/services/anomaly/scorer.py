SEVERITY_MAP = {
    "unknown_vendor": 0.4,
    "very_strong_signal": 0.7,
    "low_signal_quality": 0.5,
    "management_storm": 0.6,
}

def compute_severity(anomaly: dict) -> float:
    return SEVERITY_MAP.get(anomaly.get("type"), 0.2)