# utils/time.py

from datetime import datetime, timezone


def now_iso() -> str:
    """
    Current UTC time in ISO 8601 format.
    """
    return datetime.now(timezone.utc).isoformat()


def parse_iso(ts: str) -> datetime:
    """
    Parse an ISO 8601 timestamp into a datetime.
    """
    return datetime.fromisoformat(ts.replace("Z", "+00:00"))
