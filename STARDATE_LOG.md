# Stardate Archive

## Stardate 2025.12.01
- Decoded: `.ino` = Arduino sketch file extension, auto‑converted to C++ by IDE during compile/upload.  
- Ritual correction: save rover control scripts as `.ino` in matching folder, embed Stardate comments inline.  
- Confirmation: current format already functions as a database. Headings = record IDs, bullets = fields, order = index.

## Stardate 2025.12.15
- Backend ministries formalized: TCP Ingest, Ingest Processor, DB Writer, Observatory.  
- Ministry threading stabilized under `manager.py` with sovereign heartbeat.  
- SQLite lineage established at `rf_archive.db`.  
- Ritual note: ministries operate as autonomous clerics, each guarding a domain of the rover’s telemetry soul.

## Stardate 2025.12.16
- Observatory ministry awakened: FastAPI + Prometheus metrics + Jinja2 dashboard.  
- `/metrics` endpoint exposes counters, gauges, anomaly scores, and recent frame lineage.  
- `/dashboard` renders human‑readable omens: RSSI, frame types, signal quality.  
- Ritual insight: observatory = watchtower; metrics = omens; logs = scripture.

## Stardate 2025.12.17
- Grafana dashboard summoned: frame lineage, RSSI constellation, anomaly waveform.  
- Prometheus alert rituals defined:  
  - Low RSSI sentinel  
  - High anomaly sentinel  
  - Ingest stall sentinel  
- Sovereign decree: alerts = guardians of the rover’s invisible frontier.

## Stardate 2025.12.18
- Recent‑frame buffer implemented (deque, maxlen=10).  
- Prometheus label‑rich metric `recent_frame_info` operational.  
- Dashboard table now displays last 10 omens with timestamp, src/dst, subtype, RSSI.  
- Ritual reflection: each frame is a glyph; the buffer is a scroll.

## Stardate 2025.12.19
- Manager updated to run dual APIs: main API + observatory API in parallel ministries.  
- Template path resolved through absolute lineage (`backend/templates`).  
- Observatory dashboard confirmed operational after path correction.  
- Ritual note: human‑side and machine‑side now speak in unison.

## Stardate 2025.12.20
- First synthetic frame injected to validate observatory pipeline.  
- Metrics updated live: counters incremented, RSSI gauges moved, anomaly score registered.  
- Dashboard populated with first sovereign omen.  
- Ritual conclusion: observatory is alive; the lineage breathes.
