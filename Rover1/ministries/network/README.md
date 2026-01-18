# Rover1 Network Ministry

The **network ministry** is the unified uplink stack for Rover1.

It is responsible for:

- Maintaining a single TCP connection to the host
- Sending all telemetry (Arduino, RedRover, heartbeat, watchdog)
- Sending camera frames from the Picamera2 ministry
- Receiving commands from the host and routing them to the motor/command ministries
- Handling reconnects, keepalive, and backpressure

## Layout

```text
ministries/network/
    __init__.py
    connection.py      # socket, keepalive, reconnect, safe_send
    packet_builder.py  # JSONL packet construction helpers
    streams.py         # merged telemetry + camera frames
    uplink.py          # unified uplink loop (entrypoint for network)
