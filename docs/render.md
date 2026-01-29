flowchart TD

    A[Arduino HW] --> B[Serial Port]
    B --> C[Reader Thread]
    C --> D[Parser HB/ACK/TEL]
    D --> E[Arduino State]

    E --> F[Arduino Stream]
    F --> G[Arduino Ingest Stream]

    subgraph Ingestion
        G --> H[Merged Stream]
        R[RF Stream] --> H
        S[Heartbeat Stream] --> H
        W[Watchdog Stream] --> H
    end

    H --> I[Unified Telemetry Generator]
    I --> J[Uplink: send_unified_uplink]
    J --> K[Connection: connect_with_retry]
    K --> L[ngrok Tunnel]
    L --> M[Host TCP Server]

    M --> N[Ingress Queue]
    N --> O[DB Writer]
    N --> P[Live Dashboard]

    P --> Q[Operator Commands]
    Q --> M

    M --> L
    L --> J
    J --> T[Command Listener]
    T --> U[handle_command_packet]
    U --> V[write_to_arduino]
    V --> A
