from fastapi import APIRouter, Response
from fastapi.responses import StreamingResponse
import host.services.frame_store as frame_store
from host.services.metrics import get_camera_fps, get_camera_last_frame_age

@router.get("/camera/fps")
def camera_fps():
    return {
        "fps": get_camera_fps(),
        "age_seconds": get_camera_last_frame_age()
    }

import time

print(">>> LOADING CAMERA ROUTER <<<")

router = APIRouter()

@router.get("/latest")
def camera_latest():
    frame = frame_store.get_latest_frame()
    if frame is None:
        return Response(status_code=404)
    return Response(content=frame, media_type="image/jpeg")


@router.get("/stream")
def camera_stream():
    """
    Provides a continuous MJPEG stream from the latest buffered frames.
    """
    boundary = "frame"

    def frame_generator():
        while True:
            frame = frame_store.get_latest_frame()
            print("STREAM LOOP TICK", frame is not None)
            # Critical fix: strict None check so valid frames always yield
            if frame is not None:
                yield (
                    b"--" + boundary.encode() + b"\r\n"
                    b"Content-Type: image/jpeg\r\n"
                    b"Content-Length: " + str(len(frame)).encode() + b"\r\n\r\n"
                    + frame + b"\r\n"
                )
            time.sleep(0.05)  # ~20 FPS pacing

    return StreamingResponse(
        frame_generator(),
        media_type=f"multipart/x-mixed-replace; boundary={boundary}"
    )

@router.get("/camera/fps")
def camera_fps():
    return {
        "fps": get_camera_fps(),
        "age_seconds": get_camera_last_frame_age()
    }
