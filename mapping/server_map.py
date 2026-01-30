from fastapi import FastAPI, Response
import sqlite3
import json
import os

app = FastAPI()

# --- Absolute paths ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

MBTILES_PATH = os.path.join(
    BASE_DIR,
    "..",
    "planetiler",
    "data",
    "output.mbtiles"
)

STYLE_PATH = os.path.join(BASE_DIR, "map", "style.json")

# --- Load style.json ---
with open(STYLE_PATH, "r") as f:
    STYLE = json.load(f)


@app.get("/map/style.json")
def get_style():
    return STYLE


@app.get("/tiles/{z}/{x}/{y}.pbf")
def get_tile(z: int, x: int, y: int):
    conn = sqlite3.connect(MBTILES_PATH)
    cur = conn.cursor()

    # MBTiles uses TMS (flipped Y)
    tms_y = (2 ** z - 1) - y

    row = cur.execute(
        "SELECT tile_data FROM tiles WHERE zoom_level=? AND tile_column=? AND tile_row=?",
        (z, x, tms_y)
    ).fetchone()

    conn.close()

    if row is None:
        return Response(status_code=204)

    return Response(content=row[0], media_type="application/x-protobuf")


# --- Allow running directly ---
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "server_map:app",
        host="0.0.0.0",
        port=8001,
        reload=False
    )
