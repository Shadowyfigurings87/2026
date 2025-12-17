# utils/mac.py

import re


def normalize_mac(mac: str | None) -> str | None:
    """
    Normalize MAC address to uppercase colon-separated form.
    Returns None if input is None or empty.
    """
    if not mac:
        return None

    # Remove non-hex characters
    cleaned = re.sub(r"[^0-9A-Fa-f]", "", mac)
    if len(cleaned) != 12:
        return mac.upper()

    parts = [cleaned[i:i+2] for i in range(0, 12, 2)]
    return ":".join(parts).upper()


def mac_to_oui(mac: str | None) -> str | None:
    """
    Extract OUI (first 3 bytes) from a normalized MAC.
    """
    norm = normalize_mac(mac)
    if not norm:
        return None
    return ":".join(norm.split(":")[0:3])
