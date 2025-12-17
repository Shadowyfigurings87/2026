# classifiers/vendor_lookup.py

from utils.mac import mac_to_oui
from classifiers.oui_map import OUI_VENDOR_MAP


def lookup_vendor(mac: str | None) -> str | None:
    """
    Return a human-readable vendor name for a MAC address, if known.
    """
    oui = mac_to_oui(mac)
    if not oui:
        return None
    return OUI_VENDOR_MAP.get(oui)
