# host/services/frame_store.py

from host.logs.wrappers import log_ingest
import uuid
from pathlib import Path

FRAMES_DIR = Path(__file__).resolve().parent.parent / "data" / "frames"

def save_frame(binary_data, ext="jpg"):
    FRAMES_DIR.mkdir(parents=True, exist_ok=True)

    fname = f"{uuid.uuid4()}.{ext}"
    path = FRAMES_DIR / fname

    try:
        with open(path, "wb") as f:
            f.write(binary_data)

        log_ingest("ingest_frame_saved", filename=fname, size=len(binary_data))
        return str(path)

    except Exception as e:
        log_ingest("ingest_frame_save_error", error=str(e))
        return None
