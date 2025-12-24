# services/severity.py

def classify_severity(score: float) -> str:
    """
    Convert a numeric anomaly score (0–1) into a severity label.
    These thresholds can be tuned later.
    """

    if score is None:
        return "unknown"

    if score < 0.20:
        return "normal"

    if score < 0.50:
        return "suspicious"

    if score < 0.80:
        return "anomalous"

    return "critical"
