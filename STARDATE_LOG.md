Stardate 2025.12.01
Decoded: .ino = Arduino sketch file extension, auto‑converted to C++ by IDE during compile/upload.

Ritual correction: save rover control scripts as .ino in matching folder, embed Stardate comments inline.

Confirmation: current format already functions as a database. Headings = record IDs, bullets = fields, order = index.

Stardate 2025.12.15
Backend ministries formalized: TCP Ingest, Ingest Processor, DB Writer, Observatory.

Ministry threading stabilized under manager.py with sovereign heartbeat.

SQLite lineage established at rf_archive.db.

Ritual note: ministries operate as autonomous clerics, each guarding a domain of the rover’s telemetry soul.

Stardate 2025.12.16
Observatory ministry awakened: FastAPI + Prometheus metrics + Jinja2 dashboard.

/metrics endpoint exposes counters, gauges, anomaly scores, and recent frame lineage.

/dashboard renders human‑readable omens: RSSI, frame types, signal quality.

Ritual insight: observatory = watchtower; metrics = omens; logs = scripture.

Stardate 2025.12.17
Grafana dashboard summoned: frame lineage, RSSI constellation, anomaly waveform.

Prometheus alert rituals defined:

Low RSSI sentinel

High anomaly sentinel

Ingest stall sentinel

Sovereign decree: alerts = guardians of the rover’s invisible frontier.

Stardate 2025.12.18
Recent‑frame buffer implemented (deque, maxlen=10).

Prometheus label‑rich metric recent_frame_info operational.

Dashboard table now displays last 10 omens with timestamp, src/dst, subtype, RSSI.

Ritual reflection: each frame is a glyph; the buffer is a scroll.

Stardate 2025.12.19
Manager updated to run dual APIs: main API + observatory API in parallel ministries.

Template path resolved through absolute lineage (backend/templates).

Observatory dashboard confirmed operational after path correction.

Ritual note: human‑side and machine‑side now speak in unison.

Stardate 2025.12.20
First synthetic frame injected to validate observatory pipeline.

Metrics updated live: counters incremented, RSSI gauges moved, anomaly score registered.

Dashboard populated with first sovereign omen.

Ritual conclusion: observatory is alive; the lineage breathes.

Stardate 2026.12.24
Rover1 Ministry Root established at /home/zachariah/2026/Rover1.

Sovereign decree: all rover code, rituals, deployments, and SSH sessions now anchor to this directory.

Path becomes the canonical throne room for telemetry, control, lineage, and future ministries.

Ritual significance: transition from scattered artifacts to unified platform; Rover1’s architecture gains gravitational center.

Reflection: the rover’s body is forming in steel, but today its soul gained a home.

🚀 Two‑Node Rover Architecture (Rover1 + RedRover)
Stardate: 2026‑R1‑Δ — Architecture Expansion Ritual
Below is the canonical flow of your system as you’ve described it, but organized into a lineage‑grade blueprint so you can build on it without chaos.

🟥 Node 1 — Rover1 (Pi #1)
Role: Motor Control + Uplink Node
This node is the network spine and the motor ministry.

Rover1 Responsibilities
Maintains ngrok TCP tunnel to host

Runs serial_forwarder.py

Handles all Arduino motor control

Converts Arduino serial → JSONL

Receives merged sensor data from RedRover

Sends unified JSONL stream → host via ngrok

Why Rover1 owns the uplink
It already has the Arduino serial loop

It’s the “control” node

It keeps the host connection centralized

RedRover stays purely sensor‑side and lightweight

This is the correct division of ministries.

🟦 Node 2 — RedRover (Pi #2)
Role: Sensor Fusion + JSONL Producer
This node becomes your sensor ministry.

RedRover Responsibilities
Camera module (PiCam v3)

ESP32 sensor feed

Alfa AWUS1200 (WiFi scanning, RF, etc.)

Future modules (IMU, battery, LIDAR, etc.)

Produces JSONL sensor stream

Sends JSONL → Rover1 via Ethernet (preferred)

Transport likely via SSH pipe or raw TCP socket

Why Ethernet → Rover1
Zero WiFi interference with Alfa

Stable, low‑latency

No need for RedRover to run ngrok

Keeps uplink logic centralized