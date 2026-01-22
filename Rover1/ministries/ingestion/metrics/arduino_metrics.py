# ministries/ingestion/metrics/arduino_metrics.py

from ministries.arduino.state import get_metrics

def get_arduino_metrics():
    """
    Returns Arduino ministry health metrics for ingestion.
    """
    return get_metrics()
