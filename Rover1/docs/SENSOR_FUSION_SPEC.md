# Rover1 Sensor Fusion Specification  
Arduino + ESP32 + Camera Integration (2026)

This document describes how Rover1 merges sensor data from multiple ministries into a unified telemetry stream.

---

## 🧩 Sensor Sources

### Arduino Ministry
- Ultrasonic distance sensors  
- Motor encoder feedback (optional)  
- IMU (optional)  
- Motor state (PWM, direction)  

### RedRover (ESP32)
- Battery voltage  
- WiFi signal strength  
- Internal temperature  
- Status flags  

### Camera Ministry
- Frame timestamps  
- JPEG size  
- FPS  
- Exposure metadata (optional)  

---

## 🔄 Fusion Pipeline

```
Arduino →\
           \
            → merged_stream() → Uplink → Cockpit
Camera  →/  
RedRover →/
```

---

## 🧠 Fusion Rules

### 1. Timestamp Alignment
Each packet includes:
```
"ts": <float>
```
All ministries use Pi system time.

### 2. Ministry Tagging
Each packet includes:
```
"ministry": "arduino" | "camera" | "esp32"
```

### 3. Non-Blocking Merge
Ingestion ministry uses:
- Queues for each ministry  
- Round‑robin consumption  
- No blocking on slow ministries  

### 4. Priority
Camera frames are high‑bandwidth → lower priority  
Arduino + ESP32 telemetry → high priority  

### 5. Unified Output Format

Example unified packet:

```json
{
  "ts": 1769379112.551,
  "ministry": "arduino",
  "motors": { "left": 120, "right": 118 },
  "sensors": { "front": 0.42 }
}
```

---

## 🛡️ Fault Tolerance

- Missing camera frames → skip  
- Missing Arduino packets → retry serial  
- Missing ESP32 packets → keep last known state  

---

This fusion spec represents the 2026 sovereign Rover1 telemetry lineage.
