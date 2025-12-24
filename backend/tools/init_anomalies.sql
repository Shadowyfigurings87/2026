-- tools/init_anomalies.sql

CREATE TABLE IF NOT EXISTS anomalies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    frame_timestamp TEXT NOT NULL,
    src_mac TEXT,
    channel INTEGER,
    frame_type TEXT,
    anomaly_score REAL,
    anomaly_severity TEXT,
    anomaly_cluster TEXT,
    device_deviation REAL,
    channel_deviation REAL
);
