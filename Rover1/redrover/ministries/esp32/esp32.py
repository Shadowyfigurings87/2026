from ministries.utils.jsonl import now_ts

def esp32_stream():
    """
    Placeholder: simulate sensor readings.
    Replace with real serial/WiFi ESP32 data later.
    """
    import time, math
    t = 0
    while True:
        temp = 20 + 5 * math.sin(t)
        hum = 40 + 10 * math.cos(t)
        yield {
            "kind": "telemetry",
            "source": "esp32",
            "rover": "RedRover",
            "ts": now_ts(),
            "data": {
                "temp": temp,
                "humidity": hum
            }
        }
        t += 0.1
        time.sleep(0.2)
