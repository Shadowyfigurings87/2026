# Rover1 Camera Pipeline Specification  
Picamera2 → JPEG Encoder → RAW Uplink → Ingestion

This document describes the full camera pipeline used by Rover1’s Camera Ministry.

---

## 1. Backend Initialization

### Picamera2 loads:
- Sensor driver (IMX708)
- Tuning file:
  ```
  /usr/share/libcamera/ipa/rpi/vc4/imx708.json
  ```
- Pipeline configuration:
  - RAW stream (1536x864)
  - Processed stream (640x480 XBGR8888)

### Backend confirms:
- Camera registered
- Unicam + ISP devices mapped
- Streams configured

---

## 2. Capture Loop

The camera ministry thread performs:

1. `picam.capture_array()`  
2. Convert to RGB888 / XBGR8888  
3. Pass frame to JPEG encoder  
4. Timestamp frame  
5. Package into frame object:
   ```json
   {
     "jpeg": <bytes>,
     "ts": <float>,
     "size": <int>
   }
   ```

---

## 3. JPEG Encoding

Encoding is performed using **simplejpeg**, which is ABI‑matched to system NumPy.

Pipeline:

```
RGB Frame → simplejpeg.encode_jpeg() → JPEG bytes
```

Encoding parameters:
- Quality: 85 (default)
- Subsampling: 4:2:0
- Optimized for low-latency rover streaming

---

## 4. RAW Uplink Client

The RAW uplink client sends frames using:

```
[len][jpeg]
```

Where:
- `len` = 4‑byte big‑endian integer
- `jpeg` = encoded frame bytes

This ensures:
- No framing ambiguity
- No delimiter issues
- High throughput
- Low latency

---

## 5. Ingestion Integration

Camera frames are fed into:

```
merged_stream()
```

The ingestion ministry merges:
- Arduino telemetry
- RedRover telemetry
- Camera frames

Each unified packet includes:
- Timestamp
- Ministry identifier
- Payload

---

## 6. Failure Recovery

If the camera backend fails:
- Picamera2 reinitializes
- Capture loop restarts
- RAW uplink reconnects
- Systemd ensures full resurrection

---

This pipeline represents the 2026 sovereign camera lineage of Rover1.
