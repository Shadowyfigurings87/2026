# host/services/frame_store.py

import uuid
from pathlib import Path

FRAMES_DIR = Path(__file__).resolve().parent.parent / "data" / "frames"

def save_frame(binary_data, ext="jpg"):
    FRAMES_DIR.mkdir(parents=True, exist_ok=True)
    fname = f"{uuid.uuid4()}.{ext}"
    path = FRAMES_DIR / fname
    with open(path, "wb") as f:
        f.write(binary_data)
    return str(path)
