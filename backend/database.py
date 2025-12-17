import sqlite3
from utils.config import get_db_path
from write_queue import db_write_queue

DB_PATH = get_db_path()

# -----------------------------------------
# READ-ONLY CONNECTION FACTORY
# -----------------------------------------

def get_read_connection():
    """
    Create a short-lived connection for read queries.
    Each call gets a fresh connection to avoid interfering
    with the dedicated writer connection.
    """
    conn = sqlite3.connect(DB_PATH, timeout=5.0, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON;")
    conn.execute("PRAGMA busy_timeout=5000;")
    return conn


def query(sql: str, params: tuple = (), logger=None):
    try:
        conn = get_read_connection()
        cur = conn.cursor()
        cur.execute(sql, params)
        rows = [dict(r) for r in cur.fetchall()]
        conn.close()
        return rows
    except Exception as e:
        if logger:
            logger.error(f"DB query error: {e} | SQL={sql} | params={params}")
        raise


def query_one(sql: str, params: tuple = (), logger=None):
    rows = query(sql, params, logger=logger)
    return rows[0] if rows else None


# -----------------------------------------
# WRITE DISPATCHER (QUEUE-BASED)
# -----------------------------------------

def execute(sql: str, params: tuple = (), logger=None):
    """
    Enqueue a write operation to be handled by the dedicated DB writer thread.
    This function does NOT write to SQLite directly.
    """
    try:
        db_write_queue.put((sql, params))
    except Exception as e:
        if logger:
            logger.error(f"DB enqueue error: {e} | SQL={sql} | params={params}")
        raise


# -----------------------------------------
# Convenience query helpers
# -----------------------------------------

def get_recent_frames(limit: int = 50):
    sql = """
        SELECT id, timestamp, frame_type, subtype, src_mac, dst_mac, bssid,
               channel, rssi, sensor_id, sensor_component_role
        FROM frames
        ORDER BY id DESC
        LIMIT ?
    """
    return query(sql, (limit,))


def get_recent_alerts(limit: int = 50):
    sql = """
        SELECT id, timestamp, alert_type, mac, sensor_id, component_role,
               severity, description
        FROM alerts
        ORDER BY id DESC
        LIMIT ?
    """
    return query(sql, (limit,))


def get_recent_channel_metrics(limit: int = 50):
    sql = """
        SELECT id, timestamp, channel, sensor_id, component_role, activity_score
        FROM channel_metrics
        ORDER BY id DESC
        LIMIT ?
    """
    return query(sql, (limit,))


def get_sensor_status(limit: int = 100):
    sql = """
        SELECT id, sensor_id, last_seen, component_mac, component_role
        FROM sensor_status
        ORDER BY last_seen DESC
        LIMIT ?
    """
    return query(sql, (limit,))


def get_system_health():
    frames = query("SELECT COUNT(*) AS count FROM frames")[0]["count"]
    alerts = query("SELECT COUNT(*) AS count FROM alerts")[0]["count"]
    sensors = query("SELECT COUNT(*) AS count FROM sensor_components")[0]["count"]

    return {
        "frames": frames,
        "alerts": alerts,
        "registered_sensors": sensors,
    }
