# ingestion/streams/watchdog_stream.py

from ministries.health.watchdog import watchdog_stream

def get_stream(check_interval=3):
    return watchdog_stream(check_interval=check_interval)
