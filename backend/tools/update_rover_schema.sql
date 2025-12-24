-- ============================================================
--  ROVER SCHEMA MIGRATION
--  Extends rf_archive.db to support Rover1 + RedRover telemetry
--  Safe to run multiple times (IF NOT EXISTS everywhere)
-- ============================================================

PRAGMA foreign_keys = ON;

---------------------------------------------------------------
-- Migration tracking table
---------------------------------------------------------------
CREATE TABLE IF NOT EXISTS schema_migrations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    applied_at TEXT NOT NULL
);

---------------------------------------------------------------
-- ROVER TELEMETRY TABLE
-- Stores all JSONL telemetry from Rover1 + RedRover
---------------------------------------------------------------
CREATE TABLE IF NOT EXISTS rover_telemetry (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts REAL NOT NULL,
    rover TEXT NOT NULL,
    source TEXT NOT NULL,
    data JSON NOT NULL
);

-- Indexes for fast queries
CREATE INDEX IF NOT EXISTS idx_rover_telemetry_ts
    ON rover_telemetry (ts);

CREATE INDEX IF NOT EXISTS idx_rover_telemetry_rover
    ON rover_telemetry (rover);

CREATE INDEX IF NOT EXISTS idx_rover_telemetry_source
    ON rover_telemetry (source);


---------------------------------------------------------------
-- ROVER COMMAND ACK TABLE
-- Stores acknowledgements from Rover1 for commands executed
---------------------------------------------------------------
CREATE TABLE IF NOT EXISTS rover_command_ack (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts REAL NOT NULL,
    rover TEXT NOT NULL,
    command_id TEXT,
    status TEXT,
    raw JSON NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_rover_command_ack_ts
    ON rover_command_ack (ts);

CREATE INDEX IF NOT EXISTS idx_rover_command_ack_rover
    ON rover_command_ack (rover);


---------------------------------------------------------------
-- ROVER COMMANDS TABLE (optional but recommended)
-- Stores commands sent from Home-Base → Rover1
---------------------------------------------------------------
CREATE TABLE IF NOT EXISTS rover_commands (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts REAL NOT NULL,
    rover TEXT NOT NULL,
    target TEXT NOT NULL,
    command JSON NOT NULL,
    status TEXT DEFAULT 'sent'
);

CREATE INDEX IF NOT EXISTS idx_rover_commands_ts
    ON rover_commands (ts);

CREATE INDEX IF NOT EXISTS idx_rover_commands_rover
    ON rover_commands (rover);


---------------------------------------------------------------
-- Record migration
---------------------------------------------------------------
INSERT OR IGNORE INTO schema_migrations (name, applied_at)
VALUES ('rover_schema_v1', datetime('now'));
