# Rover1 Camera Pipeline (Mermaid Diagram)

```mermaid
flowchart TD

    A[CameraMinistry Thread] --> B[Picamera2 Initialization]
    B --> C[Configure Sensor + Streams]
    C --> D[Start Capture Loop]

    D --> E[Acquire Frame from Picamera2]
    E --> F[Convert to RGB888 / XBGR8888]
    F --> G[Encode JPEG via simplejpeg]
    G --> H[Frame Object {jpeg, ts, size}]

    H --> I[RAW Uplink Client]
    I --> J[Send [len][jpeg] to Remote Host]

    H --> K[Ingestion Ministry]
    K --> L[merged_stream() yields camera frames]

    L --> M[Unified Uplink Ministry]
    M --> N[Send Telemetry Packet]
```
