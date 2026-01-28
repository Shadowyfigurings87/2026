from fastapi import APIRouter
from host.services.camera.server import get_fps, frame_buffer

router = APIRouter()

@router.get("/fps")
def camera_fps():
    return {"fps": get_fps()}

@router.get("/latest")
def camera_latest():
    frame = frame_buffer.latest()
    if frame is None:
        return {"status": "no_frame"}
    return {"status": "ok", "size": len(frame)}
