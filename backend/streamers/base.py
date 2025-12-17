# streamers/table.py

import asyncio
from starlette.websockets import WebSocketDisconnect

import db
from utils.config import get_poll_interval
from filters import apply_filter_to_row


async def stream_table(websocket, table: str):
    """
    Generic streaming loop for a single table with optional filters.
    """
    await websocket.accept()
    last_id = 0
    poll_interval = get_poll_interval()

    # Extract filters from query params
    params = websocket.query_params

    sensor_id = params.get("sensor_id")
    if sensor_id is not None:
        try:
            sensor_id = int(sensor_id)
        except ValueError:
            sensor_id = None

    channel = params.get("channel")
    if channel is not None:
        try:
            channel = int(channel)
        except ValueError:
            channel = None

    mac = params.get("mac")
    if mac is not None:
        mac = mac.lower()

    try:
        while True:
            rows = db.query(
                f"SELECT * FROM {table} WHERE id > ? ORDER BY id ASC",
                (last_id,)
            )

            for row in rows:
                last_id = row["id"]

                # Apply row-level filters
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
        print(f"WebSocket disconnected from table: {table}")

    except Exception as e:
        print(f"WebSocket error in {table}: {e}")
