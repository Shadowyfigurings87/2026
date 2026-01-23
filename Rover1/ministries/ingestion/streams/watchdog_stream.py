# ingestion/streams/watchdog_stream.py

from Rover1.ministries.health.watchdog import watchdog_stream

def get_stream(check_interval=3):
    return watchdog_stream(check_interval=check_interval)
