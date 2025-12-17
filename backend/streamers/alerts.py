# streamers/alerts.py

import asyncio
from starlette.websockets import WebSocketDisconnect

import db
from utils.config import get_poll_interval


async def stream_alerts(websocket):
    """
    Stream alerts with optional filtering:
      /ws/alerts?sensor_id=1&mac=AA:BB:CC:DD:EE:FF
    """
    await websocket.accept()
    poll_interval = get_poll_interval()
    last_id = 0

    params = websocket.query_params

    # Normalize filter types
    sensor_id = params.get("sensor_id")
    if sensor_id is not None:
        try:
            sensor_id = int(sensor_id)
        except ValueError:
            sensor_id = None

    mac = params.get("mac")
    if mac is not None:
        mac = mac.lower()

    try:
        while True:
            rows = db.query(
                """
                SELECT id, timestamp, alert_type, mac, sensor_id,
                       component_role, severity, description
                FROM alerts
                WHERE id > ?
                ORDER BY id ASC
                """,
                (last_id,)
            )

            for row in rows:
                last_id = row["id"]

                # Apply filters
                if sensor_id is not None and row.get("sensor_id") != sensor_id:
                    continue

                if mac is not None:
                    row_mac = (row.get("mac") or "").lower()
                    if not row_mac.startswith(mac):
                        continue

                await websocket.send_json(row)

            await asyncio.sleep(poll_interval)

    except WebSocketDisconnect:
        print("WebSocket disconnected from alerts")

    except Exception as e:
        print(f"Alert stream error: {e}")
