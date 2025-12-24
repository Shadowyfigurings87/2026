from ministries.utils.jsonl import now_ts

def alfa_stream():
    """
    Placeholder for Alfa AWUS1200 WiFi scan.
    In the future, wrap 'iw', 'nmcli', or scapy results here.
    """
    import time
    while True:
        yield {
            "kind": "telemetry",
            "source": "alfa",
            "rover": "RedRover",
            "ts": now_ts(),
            "data": {
                "ssid": "ExampleNet",
                "rssi": -60
            }
        }
        time.sleep(1.0)
