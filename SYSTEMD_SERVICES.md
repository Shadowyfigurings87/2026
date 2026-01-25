# Rover1 / Host — systemd Service Map

## Services

### 1. api.service

- **Role:** Launches the host stack (ingestion, DB writer, API, camera server).  
- **ExecStart:** Runs `python -m host.main` from project root using venv.

**Example unit:**

```ini
[Unit]
Description=Rover1 Host API and Ingestion
After=network.target

[Service]
Type=simple
WorkingDirectory=/home/zachariah/2026
Environment="PATH=/home/zachariah/2026/venv/bin"
ExecStart=/home/zachariah/2026/venv/bin/python -m host.main
Restart=on-failure
RestartSec=3
User=zachariah
Group=zachariah

[Install]
WantedBy=multi-user.target
