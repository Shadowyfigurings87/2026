# utils/mac.py

import os
import csv
from functools import lru_cache

_OUI_MAP = None

def _load_oui_map():
    global _OUI_MAP
    if _OUI_MAP is not None:
        return _OUI_MAP

    base_dir = os.path.dirname(os.path.dirname(__file__))
    oui_path = os.path.join(base_dir, "data", "vendors_oui.csv")

    mapping = {}

    if not os.path.exists(oui_path):
        _OUI_MAP = mapping
        return mapping

    with open(oui_path, newline="") as f:
        reader = csv.reader(f)
        for row in reader:
            if not row or len(row) < 2:
                continue
            prefix, vendor = row[0].strip(), row[1].strip()
            # Normalize OUI as first 6 hex chars, uppercase, no separators
            prefix = prefix.replace(":", "").replace("-", "").upper()[:6]
            if prefix:
                mapping[prefix] = vendor

    _OUI_MAP = mapping
    return mapping


@lru_cache(maxsize=4096)
def lookup_vendor(mac: str | None) -> str | None:
    """
    Fast OUI-based vendor lookup.

    - Normalizes MAC
    - Uses in-memory prefix map
    - Cached per MAC
    """
    if not mac:
        return None

    mac_norm = mac.replace(":", "").replace("-", "").upper()
    if len(mac_norm) < 6:
        return None

    prefix = mac_norm[:6]
    mapping = _load_oui_map()
    return mapping.get(prefix)
