from fastapi import APIRouter, HTTPException
from typing import Optional
import sqlite3
import os
import time
from fastapi import APIRouter, Request

router = APIRouter(prefix="/rover", tags=["rover"])

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "rf_archive.db")


def query(sql, params=()):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute(sql, params)
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def execute(sql, params=()):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(sql, params)
    conn.commit()
    conn.close()


# ---------------------------------------------------------
# GET /rover/status
# ---------------------------------------------------------
@router.get("/status")
def rover_status():
    # Latest telemetry per source
    sources = ["arduino", "esp32", "alfa", "camera"]

    status = {}
    for src in sources:
        rows = query(
            """
            SELECT * FROM rover_telemetry
            WHERE source = ?
            ORDER BY ts DESC
            LIMIT 1
            """,
            (src,)
        )
        status[src] = rows[0] if rows else None

    # Heartbeat logic
    now = time.time()
    for src, row in status.items():
        if row:
            row["alive"] = (now - row["ts"]) < 10
        else:
            status[src] = {"alive": False}

    return {"status": status}


# ---------------------------------------------------------
# GET /rover/telemetry/{source}
# ---------------------------------------------------------
@router.get("/telemetry/{source}")
def rover_telemetry(source: str, limit: int = 50):
    rows = query(
        """
        SELECT * FROM rover_telemetry
        WHERE source = ?
        ORDER BY ts DESC
        LIMIT ?
        """,
        (source, limit)
    )
    return {"source": source, "count": len(rows), "data": rows}


# ---------------------------------------------------------
# POST /rover/command
# ---------------------------------------------------------
@router.post("/command")
def rover_command(cmd: dict):
    """
    Expected JSON:
    {
        "target": "motor",
        "direction": "FWD",
        "speed": 120
    }
    """

    if "target" not in cmd:
        raise HTTPException(status_code=400, detail="Missing 'target' field")

    ts = time.time()

    # Insert into DB
    execute(
        """
        INSERT INTO rover_commands (ts, rover, target, command, status)
        VALUES (?, ?, ?, json(?), 'sent')
        """,
        (ts, "Rover1", cmd["target"], json.dumps(cmd))
    )

    # Push into TCP downlink queue
    from backend.services.tcp_ingest import command_queue
    command_queue.put({
        "kind": "command",
        "ts": ts,
        "rover": "Rover1",
        **cmd
    })

    return {"status": "queued", "command": cmd}


# ---------------------------------------------------------
# GET /rover/commands/recent
# ---------------------------------------------------------
@router.get("/commands/recent")
def recent_commands(limit: int = 20):
    rows = query(
        """
        SELECT * FROM rover_commands
        ORDER BY ts DESC
        LIMIT ?
        """,
        (limit,)
    )
    return {"count": len(rows), "commands": rows}

@router.get("/camera")
def rover_camera_page(request: Request):
    return templates.TemplateResponse("rover_camera.html", {"request": request})

@router.get("/camera/stream")
def rover_camera_stream():
    return RedirectResponse("http://your-camera-ip-or-stream-url")

