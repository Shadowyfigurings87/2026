# streamers/unified.py

import asyncio
from starlette.websockets import WebSocketDisconnect

import db
from filters import apply_filter_to_row
from utils.config import get_poll_interval


async def stream_all(websocket):
    """
    Unified event stream with optional filters:
      /ws/all?sensor_id=1&channel=6&mac=AA:BB:CC:DD:EE:FF
    """
    await websocket.accept()
    poll_interval = get_poll_interval()

    params = websocket.query_params

    # sensor_id filter
    sensor_id = params.get("sensor_id")
    if sensor_id is not None:
        try:
            sensor_id = int(sensor_id)
        except ValueError:
            sensor_id = None

    # channel filter
    channel = params.get("channel")
    if channel is not None:
        try:
            channel = int(channel)
        except ValueError:
            channel = None

    # mac filter
    mac = params.get("mac")
    if mac is not None:
        mac = mac.lower()

    last_ids = {
        "frames": 0,
        "alerts": 0,
        "channel_metrics": 0,
        "sensor_status": 0,
    }

    try:
        while True:
            for table in last_ids.keys():
                rows = db.query(
                    f"SELECT * FROM {table} WHERE id > ? ORDER BY id ASC",
                    (last_ids[table],)
                )

                for row in rows:
                    last_ids[table] = row["id"]

                    # Apply filters per table
                    if table == "frames":
                        if not apply_filter_to_row(
                            row,
                            sensor_id=sensor_id,
                            channel=channel,
                            mac=mac
                        ):
                            continue

                    elif table == "channel_metrics":
                        if sensor_id is not None and row.get("sensor_id") != sensor_id:
                            continue
                        if channel is not None and row.get("channel") != channel:
                            continue

                    elif table == "alerts":
                        if sensor_id is not None and row.get("sensor_id") != sensor_id:
                            continue
                        if mac is not None:
                            row_mac = (row.get("mac") or "").lower()
                            if not row_mac.startswith(mac):
                                continue

                    elif table == "sensor_status":
                        if sensor_id is not None and row.get("sensor_id") != sensor_id:
                            continue

                    await websocket.send_json({
                        "table": table,
                        "data": row,
                    })

            await asyncio.sleep(poll_interval)

    except WebSocketDisconnect:
        print("Unified WebSocket disconnected")

    except Exception as e:
        print(f"Unified WebSocket error: {e}")
