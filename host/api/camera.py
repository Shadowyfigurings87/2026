# host/api/camera.py

from fastapi import APIRouter, HTTPException
from pathlib import Path
import base64
from host.logs.wrappers import log_camera

# Directory where frames are stored
FRAMES_DIR = Path(__file__).resolve().parent.parent / "data" / "frames"

router = APIRouter()


# ---------------------------------------------------------
# LIST RECENT FRAMES
# ---------------------------------------------------------

@router.get("/recent")
def list_recent_frames(limit: int = 20):
    """
    Returns a list of recent frame filenames.
    Frontend can request individual frames by ID.
    """
    if not FRAMES_DIR.exists():
        log_camera("camera_frames_dir_missing", path=str(FRAMES_DIR))
        return {"frames": []}

    frames = sorted(
        FRAMES_DIR.glob("*.jpg"),
        key=lambda p: p.stat().st_mtime,
        reverse=True
    )[:limit]

    frame_list = [f.name for f in frames]

    log_camera("camera_recent_frames_listed", count=len(frame_list))

    return {"frames": frame_list}


# ---------------------------------------------------------
# GET A SINGLE FRAME (BASE64 ENCODED)
# ---------------------------------------------------------

@router.get("/frame/{frame_id}")
def get_frame(frame_id: str):
    """
    Returns a single frame as base64 JPEG.
    This is frontend-friendly and avoids binary transport issues.
    """
    frame_path = FRAMES_DIR / frame_id

    if not frame_path.exists():
        log_camera("camera_frame_not_found", frame_id=frame_id)
        raise HTTPException(status_code=404, detail="Frame not found")

    try:
        data = frame_path.read_bytes()
        b64 = base64.b64encode(data).decode("utf-8")

        log_camera("camera_frame_served", frame_id=frame_id, size=len(data))

        return {
            "frame_id": frame_id,
            "content_type": "image/jpeg",
            "b64": b64,
        }

    except Exception as e:
        log_camera("camera_frame_read_error", frame_id=frame_id, error=str(e))
        raise HTTPException(status_code=500, detail="Error reading frame")


# ---------------------------------------------------------
# RAW BINARY ENDPOINT (OPTIONAL)
# ---------------------------------------------------------

@router.get("/frame_raw/{frame_id}")
def get_frame_raw(frame_id: str):
    """
    Optional: return raw binary JPEG for direct <img src="/..."> usage.
    """
    frame_path = FRAMES_DIR / frame_id

    if not frame_path.exists():
        log_camera("camera_frame_not_found_raw", frame_id=frame_id)
        raise HTTPException(status_code=404, detail="Frame not found")

    try:
        data = frame_path.read_bytes()
        log_camera("camera_frame_raw_served", frame_id=frame_id, size=len(data))
        return Response(content=data, media_type="image/jpeg")

    except Exception as e:
        log_camera("camera_frame_raw_error", frame_id=frame_id, error=str(e))
        raise HTTPException(status_code=500, detail="Error reading frame")
