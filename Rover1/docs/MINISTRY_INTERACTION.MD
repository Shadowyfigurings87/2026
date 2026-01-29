# Rover1 Ministry Interaction Model  
Inter-Ministry Communication & Data Flow (2026)

This document describes how Rover1’s ministries interact, communicate, and synchronize during operation.

---

## 🧩 Ministry Overview

- **Arduino Ministry** — motor control, sensor polling, serial telemetry  
- **Camera Ministry** — Picamera2 capture, JPEG encoding, RAW uplink  
- **RedRoverLink** — ESP32 telemetry server  
- **Ingestion Ministry** — merges all telemetry streams  
- **Uplink Ministry** — sends unified telemetry to cockpit  
- **Heartbeat Loop** — system health indicator  

---

## 🔄 Interaction Diagram

```
Arduino →\
           \
            → Ingestion → Uplink → Remote Cockpit
Camera  →/  
RedRover →/
```

---

## 📡 Ministry Responsibilities

### Arduino Ministry
- Reads serial packets  
- Emits structured telemetry  
- Provides motor/sensor state  

### Camera Ministry
- Captures frames  
- Encodes JPEG  
- Sends RAW uplink  
- Provides frame metadata  

### RedRoverLink
- Accepts TCP connections  
- Receives JSON telemetry  
- Forwards to ingestion  

### Ingestion Ministry
- Merges:
  - Arduino packets  
  - Camera frames  
  - RedRover telemetry  
- Produces unified packets  

### Uplink Ministry
- Sends merged packets to remote cockpit  
- Reconnects automatically  

---

## 🧠 Synchronization Model

- Ministries run in independent threads  
- Ingestion uses non-blocking queues  
- Camera and Arduino operate at different rates  
- RedRover telemetry is event-driven  
- Uplink ministry consumes merged stream  

---

## 🛡️ Failure Handling

- Any ministry crash → systemd restarts entire stack  
- Serial disconnect → Arduino ministry auto-reconnects  
- Camera backend failure → Picamera2 reinitializes  
- Uplink failure → reconnect loop  

---

This ministry interaction model reflects the 2026 sovereign Rover1 architecture.
