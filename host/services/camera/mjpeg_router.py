# host/services/camera/mjpeg_router.py

from fastapi.responses import StreamingResponse
from .server import frame_buffer

def mjpeg_stream():
    boundary = "--frame"

    while True:
        frame = frame_buffer.latest()
        if frame is None:
            continue

        yield (
            boundary.encode() + b"\r\n"
            + b"Content-Type: image/jpeg\r\n"
            + b"Content-Length: " + str(len(frame)).encode() + b"\r\n\r\n"
            + frame + b"\r\n"
        )

def register_routes(app):
    @app.get("/camera/mjpeg")
    def camera_mjpeg():
        return StreamingResponse(
            mjpeg_stream(),
            media_type="multipart/x-mixed-replace; boundary=frame"
        )
