# Rover1 — Sovereign Ministry Stack  
Autonomous Multi‑Ministry Rover Platform (2026 Edition)

Rover1 is a fully integrated, multi‑node robotics platform built on Raspberry Pi OS (Bookworm), featuring:

- Arduino‑based motor and sensor ministry  
- Picamera2‑powered camera ministry  
- ESP32‑based RedRover telemetry node  
- Unified ingestion pipeline  
- Real‑time uplink to remote cockpit  
- Systemd‑managed autonomous boot sequence  
- Modular “ministry” architecture for clean expansion  

This document provides a complete overview of Rover1’s architecture, setup, dependencies, and operational procedures.

---

## 📦 Project Structure

```
Rover1/
├── main.py
├── SYSTEMD.md
├── REQUIREMENTS.md
├── ministries/
│   ├── arduino/
│   ├── camera/
│   ├── control/
│   ├── health/
│   ├── ingestion/
│   ├── network/
│   └── utils/
├── redrover/          # ESP32-side reference code
├── redrover_link/     # TCP server for RedRover telemetry
└── venv/              # Python virtual environment
```

---

## 🚀 Boot Sequence (Systemd)

Rover1 launches automatically at boot via:

```
/etc/systemd/system/rover1.service
```

The service:

- Activates the venv  
- Exposes the correct PYTHONPATH  
- Runs Rover1 as a Python package (`python -m Rover1.main`)  
- Restarts automatically on failure  
- Streams logs to `journalctl`  

See `SYSTEMD.md` for full details.

---

## 🛰️ Ministries Overview

### **Arduino Ministry**
- Manages motor control, sensor polling, and serial telemetry  
- Auto‑detects Arduino Mega via `/dev/serial/by-id/...`  
- Provides heartbeat and state updates  

### **Camera Ministry**
- Uses Picamera2 + OpenCV  
- Provides JPEG-encoded frames  
- Streams RAW uplink to remote cockpit  
- Runs in its own thread with configurable FPS  

### **RedRover Ministry (ESP32)**
- ESP32 node sends telemetry to Rover1  
- Rover1 listens on TCP port `9000`  
- JSON packets are merged into ingestion pipeline  

### **Ingestion Ministry**
- Merges Arduino, Camera, and RedRover streams  
- Provides unified telemetry generator  

### **Uplink Ministry**
- Sends merged telemetry to remote host  
- Uses ngrok TCP tunnels for WAN access  

---

## 🌐 Static IP Setup for RedRover (ESP32)

RedRover must always appear at:

```
192.168.5.1
```

Rover1 must appear at:

```
192.168.5.2
```

### **On Rover1 (Raspberry Pi)**

Edit:

```
sudo nano /etc/dhcpcd.conf
```

Add:

```
interface wlan0
static ip_address=192.168.5.2/24
static routers=192.168.5.1
static domain_name_servers=8.8.8.8
```

Restart networking:

```
sudo systemctl restart dhcpcd
```

### **On RedRover (ESP32)**

In your ESP32 WiFi AP code:

```cpp
WiFi.softAP("RedRover", "password", 1, false, 1);
WiFi.softAPConfig(
    IPAddress(192,168,5,1),
    IPAddress(192,168,5,1),
    IPAddress(255,255,255,0)
);
```

This ensures:

- ESP32 = gateway + AP  
- Rover1 = static client  
- RedRoverLink server always receives packets  

---

## 🧪 Testing the System

### Check service status:

```
sudo systemctl status rover1.service
```

### Follow logs:

```
sudo journalctl -u rover1.service -f
```

You should see:

- Arduino ministry ready  
- Camera backend initialized  
- RedRoverLink server listening  
- Telemetry packets from ESP32  
- Heartbeats every 5 seconds  

---

## 🛠️ Development Notes

- Rover1 must be run as a **Python package**, not a script  
- The venv must have `include-system-site-packages = true`  
- Picamera2 and OpenCV must be installed via apt, not pip  
- NumPy must be system-provided to avoid ABI conflicts  

---

## 📚 Documentation

- `SYSTEMD.md` — systemd service configuration  
- `REQUIREMENTS.md` — Python + system dependencies  
- `scan.txt` — hardware scan logs  
- `redrover/` — ESP32 reference code  

---

## 🏁 Status

Rover1 is fully operational under systemd with:

- Arduino ministry  
- Camera ministry  
- RedRover telemetry  
- Ingestion pipeline  
- Unified uplink  
- Autonomous boot  
- Stable heartbeat  

This repository represents the 2026 sovereign lineage of Rover1.
