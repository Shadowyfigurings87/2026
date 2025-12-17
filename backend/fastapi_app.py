from streamers.frames import stream_frames
from streamers.alerts import stream_alerts
from streamers.channels import stream_channels
from streamers.sensors import stream_sensors
from streamers.unified import stream_all

@app.websocket("/ws/all")
async def ws_all(websocket: WebSocket):
    await stream_all(websocket)

@app.websocket("/ws/frames")
async def ws_frames(websocket: WebSocket):
    await stream_frames(websocket)

@app.websocket("/ws/alerts")
async def ws_alerts(websocket: WebSocket):
    await stream_alerts(websocket)

@app.websocket("/ws/channels")
async def ws_channels(websocket: WebSocket):
    await stream_channels(websocket)

@app.websocket("/ws/sensors")
async def ws_sensors(websocket: WebSocket):
    await stream_sensors(websocket)
