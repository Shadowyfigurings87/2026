from fastapi import APIRouter, Response
from host.services.frame_store import get_latest_frame
import asyncio

router = APIRouter()

@router.get("/latest")
async def latest_frame():
    frame_bytes = get_latest_frame()
    if frame_bytes is None:
        return Response(status_code=404)
    return Response(content=frame_bytes, media_type="image/jpeg")


@router.get("/stream")
async def mjpeg_stream():
    async def frame_generator():
        boundary = "frame"
        while True:
            frame = get_latest_frame()
            if frame:
                yield (
                    f"--{boundary}\r\n"
                    f"Content-Type: image/jpeg\r\n"
                    f"Content-Length: {len(frame)}\r\n\r\n"
                ).encode("utf-8") + frame + b"\r\n"
            await asyncio.sleep(0.1)  # ~10 FPS

    return Response(
        frame_generator(),
        media_type="multipart/x-mixed-replace; boundary=frame"
    )
