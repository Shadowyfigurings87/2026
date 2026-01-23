Layer	Ministry / Component	Role
Hardware	Arduino, Camera	Raw signals, sensors, motion
Rover Core	Arduino, Camera, Ingestion	Turn signals into structured telemetry
Network	Uplink, Connection, Packets	Tunnel telemetry + commands
Host	TCP server, DB, Dashboard	Persist, analyze, and visualize
Control	Command router, Motor ctrl	Turn host intent into rover actions
[Arduino HW]
    │  (USB/serial)
    ▼
[serial_link.open_serial_port()]
    │
    ▼
[threads.arduino_reader_thread()]
    │  reads raw lines
    │  updates state.latest_line
    ▼
[parser.parse_line()]
    │  HB / ACK / TEL / RAW → dict
    │  updates heartbeat + ack state
    ▼
[state.*]
    - latest_line
    - metrics
    - last_command / last_ack / heartbeat_ts
    ▼
[service.arduino_stream()]
    │  watches latest_line
    │  yields parsed event dicts
    ▼
[ingestion/streams/arduino_stream.arduino_ingest_stream()]
    │  normalizes ministry + ts + timestamp
    ▼
[ingestion.base.merged_stream()]
[arduino_ingest_stream()]  ← Arduino ministry
[redrover_stream()]        ← RF / rover link
[heartbeat_stream()]       ← synthetic system heartbeat
[watchdog_stream()]        ← internal health checks
    │
    ▼
[merged_stream()]
    - jitter smoothing per ministry
    - ministry tagging
    - timestamp normalization
    - Arduino metrics emission
    - queue pressure annotation
    ▼
[unified telemetry generator] → passed to uplink
[merged_stream()]  → generator of telemetry dicts
    │
    ▼
[uplink.send_unified_uplink(host, port, telemetry_gen)]
    │
    ├─ handshake_packet()  (on connect)
    ├─ heartbeat_packet()  (on idle)
    ├─ telemetry_packet()  (per event)
    │
    ▼
[connection.connect_with_retry()]
    │  TCP_NODELAY, retry loop
    ▼
[ngrok TCP tunnel → host]
    ▲
    │
[_command_listener()]
    │  reads JSONL from host
    │  safe_parse()
    │  handle_command_packet()
    ▼
[motor / control ministries]
[Host dashboard / operator]
    │  sends command JSON
    ▼
[Host TCP server]
    │  writes JSONL down tunnel
    ▼
[_command_listener() in uplink]
    │  safe_parse()
    ▼
[handle_command_packet(packet)]
    │  translates to Arduino command strings
    ▼
[arduino.commands.write_to_arduino(msg)]
    │  serial write (thread-safe)
    ▼
[Arduino HW executes motion]
    │
    └─ emits ACK / TEL back into telemetry loop
                 ┌────────────────────────────────────────────────────┐
                 │                     HOST                           │
                 │                                                    │
                 │  [TCP Server]  ←─── JSONL ───  [Uplink Ministry]   │
                 │      │                               ▲             │
                 │      ▼                               │             │
                 │  [Ingress Queue]                     │             │
                 │      │                               │             │
                 │      ├──→ [DB Writer]                │             │
                 │      └──→ [Live Dashboard]           │             │
                 │                                        Commands    │
                 │  [Command API / UI] ─── JSONL ───────┘             │
                 └────────────────────────────────────────────────────┘
                                      ▲
                                      │  ngrok TCP tunnel
                                      ▼
┌────────────────────────────────────────────────────────────────────────────┐
│                                ROVER1                                      │
│                                                                            │
│  [Arduino HW] ── USB ──> [Arduino Ministry]                                │
│      │                     - discovery / serial_link                       │
│      │                     - threads (reader)                              │
│      │                     - parser (HB/ACK/TEL/RAW)                       │
│      │                     - state (metrics, heartbeat, ack, latest_line)  │
│      │                     - commands (write_to_arduino)                   │
│      ▼                                                                     │
│  [Camera HW] ──> [Camera Ministry]                                         │
│                                                                            │
│  [Ingestion Ministry]                                                      │
│      - arduino_ingest_stream()                                            │
│      - redrover_stream()                                                  │
│      - heartbeat_stream()                                                 │
│      - watchdog_stream()                                                  │
│      - merged_stream()  ────────────────┐                                  │
│                                         │ telemetry_generator              │
│  [Network / Uplink Ministry]            │                                  │
│      - connection.connect_with_retry()  │                                  │
│      - packet_builder.*_packet()        ▼                                  │
│      - uplink.send_unified_uplink() ── TCP ──> HOST                        │
│             ▲                                      ▲                       │
│             │                                      │                       │
│     [_command_listener()] <── JSONL commands ─────┘                       │
│             │                                                              │
│             ▼                                                              │
│     [Control / Motor Ministry]                                             │
│             │                                                              │
│             └── write_to_arduino() → Arduino HW                            │
│                                                                            │
└────────────────────────────────────────────────────────────────────────────┘
