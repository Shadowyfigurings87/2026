# Rover1 Systemd Service  
Autonomous Boot & Ministry Orchestration (2026)

This document describes the systemd unit that launches the Rover1 Sovereign Ministry Stack at boot.  
The service ensures:

- Automatic startup on boot  
- Automatic restart on failure  
- Correct Python virtual environment activation  
- Correct package import path resolution  
- Stable, persistent operation of all ministries  
- Clean integration with Raspberry Pi OS (Bookworm)  

---

## 📍 Service File Location

The active service file is stored at:

```
/etc/systemd/system/rover1.service
```

This file is owned by the system and must be edited with `sudo`.

---

## 🛠️ Rover1 Systemd Unit Definition

Paste this exact content into:

```
sudo nano /etc/systemd/system/rover1.service
```

```
[Unit]
Description=Rover1 Sovereign Ministry Stack
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=kali
WorkingDirectory=/home/kali/2026/Rover1

ExecStart=/home/kali/2026/Rover1/venv/bin/python -m Rover1.main

Environment=PYTHONPATH=/home/kali/2026
Environment=VIRTUAL_ENV=/home/kali/2026/Rover1/venv
Environment=PATH=/home/kali/2026/Rover1/venv/bin:/usr/bin:/bin
Environment=PYTHONUNBUFFERED=1

Restart=always
RestartSec=3

StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

---

## 🧩 Why This Service Works

### **1. Runs Rover1 as a Python package**
Using:

```
python -m Rover1.main
```

ensures Python treats the project root as a package, enabling all imports.

### **2. Correct PYTHONPATH**
Systemd does not automatically expose the project root.  
This line fixes it:

```
Environment=PYTHONPATH=/home/kali/2026
```

### **3. Correct venv activation**
Systemd does not “activate” venvs.  
These lines replicate activation:

```
Environment=VIRTUAL_ENV=/home/kali/2026/Rover1/venv
Environment=PATH=/home/kali/2026/Rover1/venv/bin:/usr/bin:/bin
```

### **4. Auto‑restart**
If any ministry crashes, systemd resurrects Rover1:

```
Restart=always
RestartSec=3
```

---

## 🔄 Managing the Service

### Reload systemd after editing:

```
sudo systemctl daemon-reload
```

### Start Rover1:

```
sudo systemctl start rover1.service
```

### Stop Rover1:

```
sudo systemctl stop rover1.service
```

### Enable at boot:

```
sudo systemctl enable rover1.service
```

### Disable at boot:

```
sudo systemctl disable rover1.service
```

### View live logs:

```
sudo journalctl -u rover1.service -f
```

---

## 🧪 Expected Boot Log Sequence

When functioning correctly, you will see:

- `[Arduino] Ministry started`
- `[CameraBackend] Picamera2 initialized`
- `[CameraMinistry] Capture loop starting`
- `[RedRoverLink] Server listening`
- `[Uplink] Connecting…`
- `[Rover1] heartbeat`

This confirms all ministries are online.

---

## 🛡️ Notes & Best Practices

- Never run Rover1 via `python main.py` under systemd — always use `-m Rover1.main`.
- Ensure the venv has `include-system-site-pack
