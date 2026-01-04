# services/anomaly/engine.py

from pathlib import Path
from datetime import datetime, timedelta, timezone
import sqlite3
import yaml

from backend.services.anomaly.rules import RULES
from backend.services.anomaly import rules as rule_module
from backend.services.anomaly.scorer import compute_severity
from backend.services.alert_engine import engine as alert_engine
from backend.utils.time import now_iso
from backend.services import observatory

# ---------------------------------------------------------------------------
# Load config
# ---------------------------------------------------------------------------

CONFIG_PATH = Path(__file__).resolve().parent.parent / "data" / "config.yaml"
config: dict = {}

if CONFIG_PATH.exists():
    with open(CONFIG_PATH, "r") as f:
        config = yaml.safe_load(f)

DB_PATH = str(
    Path(__file__).resolve().parent.parent.parent / "data" / "rf_archive.db"
)

SUPPRESSION_WINDOW = timedelta(
    minutes=config.get("suppression", {}).get("window_minutes", 5)
)


# ---------------------------------------------------------------------------
# DB helpers
# ---------------------------------------------------------------------------

def _query(sql, params=()):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        cur = conn.cursor()
        cur.execute(sql, params)
        return cur.fetchall()
    finally:
        conn.close()


def _execute(sql, params=()):
    conn = sqlite3.connect(DB_PATH)
    try:
        cur = conn.cursor()
        cur.execute(sql, params)
        conn.commit()
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Main rule-based anomaly engine
# ---------------------------------------------------------------------------

def analyze_frame(frame: dict, identity_map: dict, cfg: dict | None = None):
    """
    Run all rule-based anomaly detectors on a single enriched frame.

    - frame: enriched frame dict (can include ML fields)
    - identity_map: MAC -> {sensor_id, role}
    - cfg: optional override config (if None, use module-level config)
    """
    if cfg is None:
        cfg = config

    triggered: list[dict] = []

    # 1. Legacy stateless RULES
    for rule in RULES:
        try:
            result = rule(frame)
            if result:
                triggered.append(result)
        except Exception as e:
            # Simple fallback logging
            print(f"[rules] error in rule {rule}: {e}")

    # 2. Heuristic rules
    try:
        triggered += rule_module.detect_rogue_ap(frame, identity_map, cfg)
    except Exception as e:
        print("[rules] rogue_ap error:", e)

    try:
        triggered += rule_module.detect_spoofing(frame, identity_map, cfg)
    except Exception as e:
        print("[rules] spoofing error:", e)

    try:
        triggered += rule_module.detect_jamming(frame, identity_map, cfg)
    except Exception as e:
        print("[rules] jamming error:", e)

    # 3. Persist + dispatch (single alert per anomaly)
    for anomaly in triggered:
        severity = compute_severity(anomaly)
        insert_alert(frame, anomaly, severity)

        enriched = {
            **frame,
            "rule_type": anomaly.get("type"),
            "rule_severity": severity,
            "rule_description": anomaly.get("description"),
            # Use a fresh timestamp for the rule event itself
            "timestamp": now_iso(),
        }

        # External alert channels (Discord/email/webhook)
        alert_engine.send_alert(enriched)

        # WebSocket / dashboard rule alerts
        observatory.broadcast_rule_alert(enriched)


# ---------------------------------------------------------------------------
# Insert alert with suppression
# ---------------------------------------------------------------------------

def insert_alert(frame: dict, anomaly: dict, severity: float):
    """
    Insert a rule-based alert into the alerts table with suppression.

    Uses (alert_type, mac) as the deduplication key within SUPPRESSION_WINDOW.
    """
    alert_type = anomaly.get("type", "unknown")
    mac = anomaly.get("mac") or frame.get("src") or frame.get("src_mac")

    # 1. Suppression check
    rows = _query(
        """
        SELECT timestamp FROM alerts
        WHERE alert_type = ? AND mac = ?
        ORDER BY timestamp DESC
        LIMIT 1
        """,
        (alert_type, mac),
    )

    if rows:
        last_time = datetime.fromisoformat(rows[0]["timestamp"])
        now = datetime.now(timezone.utc)
        if now - last_time < SUPPRESSION_WINDOW:
            return  # suppressed

    # 2. Insert new alert
    _execute(
        """
        INSERT INTO alerts (
            timestamp,
            alert_type,
            mac,
            sensor_id,
            component_role,
            severity,
            description
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            now_iso(),
            alert_type,
            mac,
            frame.get("sensor_id"),
            frame.get("sensor_component_role"),
            severity,
            anomaly.get("description", "no description"),
        ),
    )
