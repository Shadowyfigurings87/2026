# streamers/frames.py

import asyncio
from starlette.websockets import WebSocketDisconnect

import db
from filters import apply_filter_to_row
from utils.config import get_poll_interval


async def stream_frames(websocket):
    """
    Stream frames with optional filtering:
      /ws/frames?sensor_id=1&channel=6&mac=AA:BB:CC:DD:EE:FF
    """
    await websocket.accept()
    poll_interval = get_poll_interval()
    last_id = 0

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

    try:
        while True:
            rows = db.query(
                """
                SELECT *
                FROM frames
                WHERE id > ?
                ORDER BY id ASC
                """,
                (last_id,)
            )

            for row in rows:
                last_id = row["id"]

                if not apply_filter_to_row(
                    row,
                    sensor_id=sensor_id,
                    channel=channel,
                    mac=mac
                ):
                    continue

                await websocket.send_json(row)

            await asyncio.sleep(poll_interval)

    except WebSocketDisconnect:
        print("WebSocket disconnected from frames")

    except Exception as e:
        print(f"Frame stream error: {e}")
