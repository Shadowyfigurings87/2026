# Rover1 Changelog (2026)  
Sovereign Lineage Record

This document records all major milestones, restorations, and upgrades performed on Rover1 during the 2026 resurrection cycle.

---

## 🗓️ January 2026

### ✔️ System Resurrection
- Rebuilt Rover1 from clean Bookworm image  
- Restored all ministries  
- Reconstructed original systemd environment  
- Repaired import path issues  
- Rebuilt venv with system site packages  
- Restored Picamera2 + OpenCV compatibility  
- Fixed NumPy/simplejpeg ABI mismatch  

### ✔️ Networking
- Re-established RedRover static IP scheme  
- Restored ESP32 telemetry  
- Reconnected uplink tunnels  

### ✔️ Camera Pipeline
- Verified IMX708 sensor  
- Restored Picamera2 backend  
- Rebuilt JPEG encoding pipeline  
- Reconnected RAW uplink  

### ✔️ Arduino Ministry
- Restored serial auto-detection  
- Rebuilt reader thread  
- Verified motor control protocol  

### ✔️ Documentation
- Added SYSTEMD.md  
- Added REQUIREMENTS.md  
- Added README.md  
- Added boot flow diagrams  
- Added camera pipeline spec  
- Added network architecture  
- Added ministry interaction model  
- Added hardware wiring diagram  
- Added motor control protocol  
- Added sensor fusion spec  

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

This changelog represents the 2026 sovereign Rover1 lineage.
