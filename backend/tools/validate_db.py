# tools/validate_db.py

import sqlite3
from backend.utils.config import get_db_path


REQUIRED_TABLES = [
    "frames",
    "alerts",
    "channel_metrics",
    "sensor_status",
    "sensor_components",
    "ingest_log",
    "rssi_calibration",
]


def main():
    db_path = get_db_path()
    print(f"[+] Validating database at: {db_path}")
    conn = sqlite3.connect(db_path)

    # Integrity check
    integrity = conn.execute("PRAGMA integrity_check;").fetchone()[0]
    if integrity == "ok":
        print("  ✓ SQLite integrity OK")
    else:
        print(f"  ✗ Integrity check failed: {integrity}")

    # Table presence
    rows = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table'"
    ).fetchall()
    tables = {r[0] for r in rows}

    missing = [t for t in REQUIRED_TABLES if t not in tables]
    if missing:
        print(f"  ✗ Missing tables: {missing}")
    else:
        print("  ✓ All required tables present")

    conn.close()


if __name__ == "__main__":
    main()
