# ingestion/streams/heartbeat_stream.py

from Rover1.ministries.health.heartbeat import heartbeat_stream

def get_stream(interval=5):
    return heartbeat_stream(interval=interval)
