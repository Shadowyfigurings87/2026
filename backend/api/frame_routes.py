# api/frame_routes.py

from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
import sqlite3
import os
from backend.utils.logging_config import log_event

router = APIRouter(prefix="/dashboard")

# Path to SQLite DB
DB_PATH = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    "data",
    "rf_archive.db"
)

# Template directory
TEMPLATES_DIR = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    "templates"
)

templates = Jinja2Templates(directory=TEMPLATES_DIR)


def query_db(sql, params=()):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        cur = conn.cursor()
        cur.execute(sql, params)
        return cur.fetchall()
    finally:
        conn.close()


# -----------------------------
# Dashboard Page Route
# -----------------------------
@router.get("/frame-explorer")
def frame_explorer_page(request: Request):
    """
    Render the Frame Explorer dashboard page.
    """
    return templates.TemplateResponse(
        "frame_explorer.html",
        {"request": request}
    )


# -----------------------------
# API Endpoints
# -----------------------------
@router.get("/api/frames/recent")
def recent_frames():
    """
    Return recent raw frames.
    """
    try:
        rows = query_db(
            """
            SELECT *
            FROM frames
            ORDER BY timestamp DESC
            LIMIT 200
            """
        )
        return [dict(r) for r in rows]

    except Exception as e:
        log_event("api", "ERROR", "recent_frames_failed", {"error": str(e)})
        return {"error": "failed_to_fetch"}


@router.get("/api/frame/{frame_id}")
def frame_details(frame_id: int):
    """
    Return details for a specific frame.
    """
    try:
        rows = query_db(
            "SELECT * FROM frames WHERE id = ? LIMIT 1",
            (frame_id,),
        )
        if not rows:
            return {"error": "not_found"}

        return dict(rows[0])

    except Exception as e:
        log_event("api", "ERROR", "frame_details_failed", {"error": str(e)})
        return {"error": "failed_to_fetch"}
