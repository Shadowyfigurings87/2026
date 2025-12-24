CREATE TABLE IF NOT EXISTS frames (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT,
    source TEXT,
    iface TEXT,
    frame_type TEXT,
    subtype TEXT,
    direction TEXT,
    src_mac TEXT,
    dst_mac TEXT,
    bssid TEXT,
    ssid TEXT,
    channel INTEGER,
    rssi INTEGER,
    rate REAL,
    channel_freq INTEGER,
    channel_flags INTEGER,
    summary TEXT,
    src_role TEXT,
    dst_role TEXT,
    bssid_role TEXT,
    sensor_id INTEGER,
    sensor_component_role TEXT,
    rssi_normalized REAL,
    signal_quality REAL,
    activity_score REAL
);

CREATE TABLE IF NOT EXISTS channel_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT,
    channel INTEGER,
    sensor_id INTEGER,
    component_role TEXT,
    activity_score REAL
);

CREATE TABLE IF NOT EXISTS sensor_status (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sensor_id INTEGER,
    last_seen TEXT,
    component_mac TEXT,
    component_role TEXT
);

CREATE TABLE IF NOT EXISTS alerts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT,
    alert_type TEXT,
    mac TEXT,
    sensor_id INTEGER,
    component_role TEXT,
    severity REAL,
    description TEXT
);

CREATE TABLE IF NOT EXISTS sensor_components (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sensor_id INTEGER,
    mac TEXT,
    role TEXT
);

CREATE TABLE IF NOT EXISTS rssi_calibration (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sensor_id INTEGER,
    component_role TEXT,
    offset INTEGER
);
