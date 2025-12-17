# filters.py

def build_frame_filter(
    sensor_id=None,
    channel=None,
    mac=None,
    role=None,
    frame_type=None,
    ssid=None,
    component_role=None,
):
    """
    Build WHERE clause and params for frames filtering (REST).
    Returns (where_sql, params_list).
    """
    where = "WHERE 1=1"
    params = []

    # Sensor ID
    if sensor_id is not None:
        where += " AND sensor_id = ?"
        params.append(sensor_id)

    # Channel
    if channel is not None:
        where += " AND channel = ?"
        params.append(channel)

    # MAC filtering (src, dst, bssid)
    if mac is not None:
        mac = mac.lower()
        where += " AND (LOWER(src_mac) LIKE ? OR LOWER(dst_mac) LIKE ? OR LOWER(bssid) LIKE ?)"
        mac_like = f"{mac}%"
        params.extend([mac_like, mac_like, mac_like])

    # Device role (AP, client, unknown)
    if role is not None:
        where += " AND (src_role = ? OR dst_role = ? OR bssid_role = ?)"
        params.extend([role, role, role])

    # Frame type (management, control, data)
    if frame_type is not None:
        where += " AND frame_type = ?"
        params.append(frame_type)

    # SSID filtering
    if ssid is not None:
        where += " AND ssid = ?"
        params.append(ssid)

    # Sensor component role (radio, antenna, etc.)
    if component_role is not None:
        where += " AND sensor_component_role = ?"
        params.append(component_role)

    return where, params


def apply_filter_to_row(
    row: dict,
    sensor_id=None,
    channel=None,
    mac=None,
    role=None,
    frame_type=None,
    ssid=None,
    component_role=None,
) -> bool:
    """
    Row-level filter for WebSocket streaming.
    Returns True if row passes filters, False if it should be dropped.
    """

    # Sensor ID
    if sensor_id is not None and row.get("sensor_id") != sensor_id:
        return False

    # Channel
    if channel is not None and row.get("channel") != channel:
        return False

    # MAC filtering
    if mac is not None:
        mac = mac.lower()
        src = (row.get("src_mac") or "").lower()
        dst = (row.get("dst_mac") or "").lower()
        bssid = (row.get("bssid") or "").lower()

        if not (
            src.startswith(mac)
            or dst.startswith(mac)
            or bssid.startswith(mac)
        ):
            return False

    # Device role
    if role is not None:
        if role not in (
            row.get("src_role"),
            row.get("dst_role"),
            row.get("bssid_role"),
        ):
            return False

    # Frame type
    if frame_type is not None and row.get("frame_type") != frame_type:
        return False

    # SSID
    if ssid is not None and row.get("ssid") != ssid:
        return False

    # Sensor component role
    if component_role is not None and row.get("sensor_component_role") != component_role:
        return False

    return True
