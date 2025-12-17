# streamers/sensors.py

import asyncio
from starlette.websockets import WebSocketDisconnect

import db
from utils.config import get_poll_interval


async def stream_sensors(websocket):
    """
    Stream sensor_status with optional filtering:
      /ws/sensors?sensor_id=1
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

    try:
        while True:
            rows = db.query(
                """
                SELECT id, sensor_id, last_seen, component_mac, component_role
                FROM sensor_status
                WHERE id > ?
                ORDER BY id ASC
                """,
                (last_id,)
            )

            for row in rows:
                last_id = row["id"]

                if sensor_id is not None and row.get("sensor_id") != sensor_id:
                    continue

                await websocket.send_json(row)

            await asyncio.sleep(poll_interval)

    except WebSocketDisconnect:
        print("WebSocket disconnected from sensors")

    except Exception as e:
        print(f"Sensor stream error: {e}")
