# Rover1 Motor Control Protocol  
Arduino Serial Command Specification (2026)

This document defines the serial protocol used by Rover1 to control motors via the Arduino ministry.

---

## 🧩 Transport

- Serial over USB  
- 115200 baud  
- Newline‑terminated JSON packets  

---

## 🕹️ Command Format

Rover1 sends motor commands to Arduino as JSON:

```json
{
  "cmd": "drive",
  "left": 120,
  "right": 118
}
```

### Fields

| Field | Type | Description |
|-------|------|-------------|
| `cmd` | string | Always `"drive"` |
| `left` | int | PWM value (0–255) |
| `right` | int | PWM value (0–255) |

---

## 🔄 Arduino Response Format

Arduino sends telemetry back:

```json
{
  "ts": 1769379112.551,
  "motors": { "left": 120, "right": 118 },
  "sensors": { "front": 0.42 }
}
```

---

## 🧠 Motor Behavior Rules

- PWM 0 = stop  
- PWM 1–127 = reverse  
- PWM 128–255 = forward  
- Direction pins set based on sign  

---

## 🛡️ Safety

- Commands outside 0–255 are clamped  
- If no command received for 1 second → motors stop  
- If serial disconnects → motors stop  

---

This protocol represents the 2026 sovereign Rover1 motor lineage.
