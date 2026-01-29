# Rover1 Boot Flow Specification  
2026 Sovereign Ministry Stack

This document describes the full boot sequence of Rover1 as orchestrated by systemd and the internal ministry architecture.

---

## 1. Systemd Initialization

1. Raspberry Pi OS reaches `network-online.target`
2. `rover1.service` is launched
3. Environment is prepared:
   - venv activated
   - PATH updated
   - PYTHONPATH set to `/home/kali/2026`
4. Rover1 is executed as a package:
   ```
   python -m Rover1.main
   ```

---

## 2. Rover1 Main Boot Sequence

### Step 1 — Arduino Ministry
- Thread created
- Serial port auto-detected via `/dev/serial/by-id/`
- Reader thread begins
- Ministry sets `arduino_ready = True`

### Step 2 — Camera Ministry
- Thread created
- Picamera2 backend initializes
- Sensor + stream configuration loaded
- Capture loop begins
- JPEG frames produced at configured FPS
- RAW uplink client connects to remote host

### Step 3 — RedRoverLink Server
- TCP server binds to `0.0.0.0:9000`
- ESP32 telemetry packets accepted
- JSON payloads forwarded to ingestion

### Step 4 — Ingestion Ministry
- `merged_stream()` generator created
- Merges:
  - Arduino telemetry
  - Camera frames
  - RedRover telemetry

### Step 5 — Uplink Ministry
- Connects to remote ngrok TCP endpoint
- Streams unified telemetry packets

### Step 6 — Heartbeat Loop
- Every 5 seconds:
  ```
  [Rover1] heartbeat
  ```

---

## 3. Failure Handling

- Any crash triggers systemd auto-restart
- Ministries restart cleanly
- Serial and camera backends reinitialize
- Uplink reconnects automatically

---

## 4. Expected Log Sequence

- `[Arduino] Ministry started`
- `[CameraBackend] Picamera2 initialized`
- `[CameraMinistry] Capture loop starting`
- `[RedRoverLink] Server listening`
- `[Ingestion] ready`
- `[Uplink] Connecting…`
- `[Rover1] heartbeat`

---

This boot flow represents the 2026 sovereign lineage of Rover1.
