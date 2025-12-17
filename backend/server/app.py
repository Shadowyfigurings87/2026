# server/app.py

from fastapi import FastAPI, WebSocket
import db

app = FastAPI(title="Sovereign RF Manager")


@app.get("/frames/latest")
def get_latest_frames(limit: int = 50):
    sql = """
        SELECT *
        FROM frames
        ORDER BY timestamp DESC
        LIMIT ?
    """
    rows = db.query(sql, (limit,))
    return [dict(r) for r in rows]


@app.get("/alerts/latest")
def get_latest_alerts(limit: int = 50):
    sql = """
        SELECT *
        FROM alerts
        ORDER BY timestamp DESC
        LIMIT ?
    """
    rows = db.query(sql, (limit,))
    return [dict(r) for r in rows]


@app.websocket("/ws/frames")
async def ws_frames(ws: WebSocket):
    await ws.accept()
    last_ts = None

    while True:
        sql = """
            SELECT *
            FROM frames
            ORDER BY timestamp DESC
            LIMIT 1
        """
        rows = db.query(sql)
        if rows:
            frame = dict(rows[0])
            if frame["timestamp"] != last_ts:
                await ws.send_json(frame)
                last_ts = frame["timestamp"]


@app.websocket("/ws/alerts")
async def ws_alerts(ws: WebSocket):
    await ws.accept()
    last_ts = None

    while True:
        sql = """
            SELECT *
            FROM alerts
            ORDER BY timestamp DESC
            LIMIT 1
        """
        rows = db.query(sql)
        if rows:
            alert = dict(rows[0])
            if alert["timestamp"] != last_ts:
                await ws.send_json(alert)
                last_ts = alert["timestamp"]
