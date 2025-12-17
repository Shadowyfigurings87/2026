-- init_rf_archive.sql
-- Phase 14: consolidated schema + identity registry for rf_archive.db

PRAGMA journal_mode=WAL;
PRAGMA synchronous=NORMAL;
PRAGMA foreign_keys=ON;
PRAGMA busy_timeout=5000;

----------------------------------------------------------------------
-- Core frames table
----------------------------------------------------------------------

CREATE TABLE frames (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    -- Raw frame context
    timestamp              TEXT NOT NULL,
    source                 TEXT,
    iface                  TEXT,

    frame_type             TEXT,
    subtype                TEXT,
    direction              TEXT,

    src_mac                TEXT,
    dst_mac                TEXT,
    bssid                  TEXT,
    ssid                   TEXT,

    channel                INTEGER,
    rssi                   INTEGER,
    rate                   REAL,
    channel_freq           INTEGER,
    channel_flags          TEXT,

    summary                TEXT,

    -- Identity and sensor awareness
    src_role               TEXT,
    dst_role               TEXT,
    bssid_role             TEXT,

    sensor_id              TEXT,
    sensor_component_role  TEXT,

    -- Feature layer
    rssi_normalized        REAL,
    signal_quality         REAL,
    activity_score         INTEGER
);

CREATE INDEX idx_frames_timestamp     ON frames (timestamp);
CREATE INDEX idx_frames_src_mac       ON frames (src_mac);
CREATE INDEX idx_frames_dst_mac       ON frames (dst_mac);
CREATE INDEX idx_frames_bssid         ON frames (bssid);
CREATE INDEX idx_frames_ssid          ON frames (ssid);
CREATE INDEX idx_frames_channel       ON frames (channel);
CREATE INDEX idx_frames_sensor_id     ON frames (sensor_id);
CREATE INDEX idx_frames_frame_type    ON frames (frame_type);

----------------------------------------------------------------------
-- Sensor components: who/what is each MAC?
----------------------------------------------------------------------

CREATE TABLE sensor_components (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sensor_id    TEXT NOT NULL,
    mac          TEXT NOT NULL,
    role         TEXT NOT NULL,
    description  TEXT
);

CREATE UNIQUE INDEX idx_sensor_mac  ON sensor_components (mac);
CREATE INDEX idx_sensor_role        ON sensor_components (role);
CREATE INDEX idx_sensor_sensor_id   ON sensor_components (sensor_id);

----------------------------------------------------------------------
-- Ingestion log: start/stop/errors
----------------------------------------------------------------------

CREATE TABLE ingest_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp  TEXT NOT NULL,
    status     TEXT NOT NULL,
    message    TEXT
);

CREATE INDEX idx_ingest_timestamp ON ingest_log (timestamp);

----------------------------------------------------------------------
-- Sensor status: lightweight heartbeats
----------------------------------------------------------------------

CREATE TABLE sensor_status (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sensor_id      TEXT NOT NULL,
    last_seen      TEXT NOT NULL,
    component_mac  TEXT,
    component_role TEXT
);

CREATE INDEX idx_sensor_status_sensor_id ON sensor_status (sensor_id);
CREATE INDEX idx_sensor_status_last_seen ON sensor_status (last_seen);

----------------------------------------------------------------------
-- RSSI calibration per sensor component
----------------------------------------------------------------------

CREATE TABLE rssi_calibration (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sensor_id      TEXT NOT NULL,
    component_role TEXT NOT NULL,
    offset         INTEGER DEFAULT 0
);

CREATE UNIQUE INDEX idx_rssi_calibration_unique
    ON rssi_calibration (sensor_id, component_role);

----------------------------------------------------------------------
-- Channel metrics: activity per channel
----------------------------------------------------------------------

CREATE TABLE channel_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp      TEXT NOT NULL,
    channel        INTEGER NOT NULL,
    sensor_id      TEXT,
    component_role TEXT,
    activity_score INTEGER
);

CREATE INDEX idx_channel_metrics_ts       ON channel_metrics (timestamp);
CREATE INDEX idx_channel_metrics_channel  ON channel_metrics (channel);

----------------------------------------------------------------------
-- Alerts: anomaly / event stream
----------------------------------------------------------------------

CREATE TABLE alerts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp      TEXT NOT NULL,
    alert_type     TEXT NOT NULL,
    mac            TEXT,
    sensor_id      TEXT,
    component_role TEXT,
    severity       REAL,
    description    TEXT
);

CREATE INDEX idx_alerts_ts        ON alerts (timestamp);
CREATE INDEX idx_alerts_type      ON alerts (alert_type);
CREATE INDEX idx_alerts_severity  ON alerts (severity);

----------------------------------------------------------------------
-- Identity Registry: Rover1 + Drixus
----------------------------------------------------------------------

INSERT INTO sensor_components (sensor_id, mac, role, description) VALUES
  -- Rover1 (Pi)
  ('rover1', 'e4:5f:01:40:10:c3', 'pi_eth',  'Rover1 Ethernet interface'),
  ('rover1', 'e4:5f:01:40:10:c4', 'pi_wifi', 'Rover1 onboard WiFi'),
  ('rover1', '00:c0:ca:b8:bf:e4', 'alfa',    'Rover1 Alfa monitor interface'),

  -- Drixus (host)
  ('drixus', '8c:ec:4b:a2:4e:fc', 'host_eth',  'Drixus Ethernet interface'),
  ('drixus', 'b2:2a:dd:c7:e4:fc', 'host_wifi', 'Drixus WiFi interface');
