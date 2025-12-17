# anomaly/scorer.py

def compute_severity(anomaly: dict) -> float:
    t = anomaly["type"]

    if t == "unknown_vendor":
        return 0.4
    if t == "very_strong_signal":
        return 0.7
    if t == "low_signal_quality":
        return 0.5
    if t == "management_storm":
        return 0.6

    return 0.2
