# Sovereign Rover Project 🚀

## Overview
This repository chronicles the evolving lineage of the Sovereign Rover — from raw hardware wiring to distributed autonomy — framed through Stardate logs and sovereign engineering rituals.  
What began as a motor‑control experiment has expanded into a full telemetry observatory, a multi‑ministry backend, and a mythic archive of breakthroughs, failures, and emergent intelligence.

## Current Capabilities

### Hardware & Control
- Remote control of 750W drive motor via WS55‑220 driver  
- Direction toggling through optocoupler circuit (Arduino pin 24)  
- Linear actuator subsystem scaffolded (BTS7960 driver planned)  
- GUI + Arduino sketches for actuator and motion lineage  

### Networking & Protocol
- ngrok‑based distributed command/status protocol  
- Remote rover control tunneled through sovereign channels  
- Telemetry expansion path for current sense, fault flags, and actuator state  

### Backend Ministries
The rover now speaks through a structured backend composed of sovereign ministries:

- **TCP Ingest Ministry**  
  Receives raw RF or telemetry frames from distributed sources.

- **Ingest Processor Ministry**  
  Normalizes, enriches, and classifies frames (control, management, data).

- **DB Writer Ministry**  
  Archives telemetry lineage into `rf_archive.db`.

- **Observatory Ministry**  
  The watchtower of the system — exposes:  
  - `/metrics` → Prometheus counters, gauges, anomaly scores  
  - `/dashboard` → Human‑readable FastAPI/Jinja2 observatory  
  - Rolling recent‑frame buffer  
  - RSSI statistics and anomaly scoring hooks  

### Monitoring & Intelligence
- **Prometheus integration** for metrics scraping  
- **Grafana dashboard** for real‑time visualization  
- **Alerting rules** for:  
  - Low RSSI  
  - High anomaly score  
  - Stalled ingest pipeline  
- Observatory heartbeat logs for sovereign introspection  

## Stardate Log
See **[STARDATE_LOG.md](STARDATE_LOG.md)** for the full chronicle of breakthroughs, regressions, and mythic engineering trials.  
Every subsystem evolution is recorded as a Stardate event — a ritual of progress.

## Goals
- Integrate linear actuator subsystem with BTS7960 driver  
- Expand telemetry lineage (current sense, fault flags, actuator state) into ngrok protocol  
- Feed actuator + sensor data into observatory metrics  
- Extend anomaly detection to behavioral and motion lineage  
- Evolve rover into autonomous form, culminating in a humanoid blueprint  

## Mythic Narrative
Every subsystem is a sovereign ritual.  
Every signal is an omen.  
Every failure is a Stardate trial.  
This repository is both a technical blueprint and a mythic chronicle — a testament to agency, persistence, and the engineering of emergent lineage.
