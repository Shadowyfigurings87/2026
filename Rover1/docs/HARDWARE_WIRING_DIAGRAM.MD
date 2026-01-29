# Rover1 Dashboard API Specification  
Unified Telemetry & Control Interface (2026)

This document defines the API used by the remote cockpit to receive telemetry and (optionally) send commands to Rover1.

---

## 📡 Telemetry Stream Format

Rover1 sends newline-delimited JSON packets over TCP.

Example packet:

```json
{
  "ts": 1769379104.2993534,
  "ministry": "camera",
  "frame_size": 8421,
  "fps": 10,
  "jpeg": "<binary omitted>"
}
```

Another example:

```json
{
  "ts": 1769379109.4124599,
  "ministry": "esp32",
  "status": "idle",
  "battery": 12.4,
  "signal": -58
}
```

Another:

```json
{
  "ts": 1769379112.551,
  "ministry": "arduino",
  "motors": { "left": 120, "right": 118 },
  "sensors": { "front": 0.42 }
}
```

---

## 🧩 Packet Fields

| Field | Type | Description |
|-------|------|-------------|
| `ts` | float | Timestamp |
| `ministry` | string | Source ministry |
| `payload` | varies | Ministry-specific data |

---

## 🛰️ Ministries & Payloads

### Arduino
```
{
  "motors": { "left": int, "right": int },
  "sensors": { "front": float, ... }
}
```

### Camera
```
{
  "jpeg": <bytes>,
  "frame_size": int,
  "fps": int
}
```

### RedRover (ESP32)
```
{
  "status": "idle" | "active",
  "battery": float,
  "signal": int
}
```

---

## 🕹️ Command Channel (Optional Future)

Commands may be added later:

```
{
  "cmd": "move",
  "left": 120,
  "right": 120
}
```

---

## 🔄 Transport

- TCP stream  
- Newline-delimited JSON  
- Binary JPEG frames sent via RAW uplink  

---

This API spec represents the 2026 sovereign Rover1 cockpit interface.
