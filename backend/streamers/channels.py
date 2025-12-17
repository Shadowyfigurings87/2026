# streamers/channels.py

import asyncio
from starlette.websockets import WebSocketDisconnect

import db
from utils.config import get_poll_interval


async def stream_channels(websocket):
    """
    Stream channel_metrics with optional filtering:
      /ws/channels?sensor_id=1&channel=6
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

    try:
        while True:
            rows = db.query(
                """
                SELECT id, timestamp, channel, sensor_id,
                       component_role, activity_score
                FROM channel_metrics
                WHERE id > ?
                ORDER BY id ASC
                """,
                (last_id,)
            )

            for row in rows:
                last_id = row["id"]

                if sensor_id is not None and row.get("sensor_id") != sensor_id:
                    continue

                if channel is not None and row.get("channel") != channel:
                    continue

                await websocket.send_json(row)

            await asyncio.sleep(poll_interval)

    except WebSocketDisconnect:
        print("WebSocket disconnected from channels")

    except Exception as e:
        print(f"Channel stream error: {e}")
