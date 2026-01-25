# Rover1 Requirements  
Complete Dependency Specification (2026)

This document lists all Python and system-level dependencies required for Rover1 to operate under systemd on Raspberry Pi OS (Bookworm).

---

# 🐍 Python Environment (venv)

Rover1 uses a Python virtual environment located at:

```
/home/kali/2026/Rover1/venv/
```

### Required pip packages:

```
pyserial
pillow
```

### IMPORTANT:

The venv **must** use system site packages.

Edit:

```
venv/pyvenv.cfg
```

Ensure:

```
include-system-site-packages = true
```

This allows the venv to access:

- system NumPy  
- system simplejpeg  
- system Picamera2  
- system OpenCV  

These cannot be installed via pip.

---

# 🧩 System Dependencies (APT)

Install all required system packages:

```
sudo apt update
sudo apt install \
    python3-picamera2 \
    python3-opencv \
    python3-numpy \
    python3-simplejpeg \
    python3-prctl \
    libcamera-apps \
    libcap-dev
```

These provide:

- Picamera2  
- OpenCV  
- libcamera backend  
- simplejpeg (ABI-matched)  
- numpy (ABI-matched)  
- prctl (required by Picamera2)  
- camera tuning files  
- sensor drivers  

---

# 🔧 Serial Device Requirements

Arduino Mega must appear under:

```
/dev/serial/by-id/
```

Example:

```
/dev/serial/by-id/usb-Arduino__www.arduino.cc__Arduino_Mega_2560_96505111011511214640-if00
```

No additional configuration required.

---

# 📡 Network Requirements

### Rover1 static IP:

```
192.168.5.2
```

### RedRover (ESP32) static AP IP:

```
192.168.5.1
```

Rover1’s systemd service depends on this addressing scheme.

---

# 🧪 Verification

Activate venv:

```
source venv/bin/activate
```

Test camera stack:

```
python3 - << 'EOF'
import cv2
from picamera2 import Picamera2
print("OK")
EOF
```

If you see `OK`, all dependencies are correct.

---

# ✔️ Status

This requirements file reflects the fully functional Rover1 system as of January 2026.
