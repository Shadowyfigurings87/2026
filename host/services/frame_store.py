# host/services/frame_store.py

from host.logs.wrappers import log_ingest
import uuid
from pathlib import Path

# ---------------------------------------------------------
# FRAME STORAGE (DISK + IN-MEMORY LATEST FRAME)
# ---------------------------------------------------------

FRAMES_DIR = Path(__file__).resolve().parent.parent / "data" / "frames"
FRAMES_DIR.mkdir(parents=True, exist_ok=True)

# In-memory latest frame (raw JPEG bytes)
latest_frame_bytes = None
latest_frame_path = None


# ---------------------------------------------------------
# SAVE FRAME TO DISK (OPTIONAL)
# ---------------------------------------------------------

def save_frame(binary_data, ext="jpg"):
    """
    Saves a frame to disk with a UUID filename.
    Returns the file path as a string.
    """
    global latest_frame_path

    fname = f"{uuid.uuid4()}.{ext}"
    path = FRAMES_DIR / fname

    try:
        with open(path, "wb") as f:
            f.write(binary_data)

        latest_frame_path = str(path)

        log_ingest(
            "ingest_frame_saved",
            filename=fname,
            size=len(binary_data)
        )

        return str(path)

    except Exception as e:
        log_ingest("ingest_frame_save_error", error=str(e))
        return None


# ---------------------------------------------------------
# IN-MEMORY LATEST FRAME (FOR /camera/latest)
# ---------------------------------------------------------

def store_latest_frame(binary_data):
    """
    Stores the most recent frame in memory for fast retrieval.
    """
    global latest_frame_bytes
    latest_frame_bytes = binary_data

    log_ingest(
        "ingest_frame_buffered",
        size=len(binary_data)
    )


def get_latest_frame():
    """
    Returns the most recently stored frame bytes (JPEG).
    Returns None if no frame has been received yet.
    """
    return latest_frame_bytes
