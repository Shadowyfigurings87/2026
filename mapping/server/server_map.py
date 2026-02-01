# /home/zachariah/2026/mapping/server/server_map.py

import os
import sqlite3
import json
import gzip
from io import BytesIO
from fastapi import FastAPI, Response, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(BASE_DIR, "..", ".."))

MBTILES_PATH = os.path.join(PROJECT_ROOT, "tilegen", "output", "florida.mbtiles")
STYLE_PATH = os.path.join(PROJECT_ROOT, "map", "style.json")
SPRITES_DIR = os.path.join(PROJECT_ROOT, "sprites")
FONTS_DIR = os.path.join(PROJECT_ROOT, "map", "fonts")

app = FastAPI(title="Sovereign Tile Server")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db():
    if not os.path.exists(MBTILES_PATH):
        raise HTTPException(500, "MBTiles not found")
    conn = sqlite3.connect(MBTILES_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def gzip_if_accepted(data: bytes) -> Response:
    buf = BytesIO()
    with gzip.GzipFile(fileobj=buf, mode="wb") as f:
        f.write(data)
    return Response(
        content=buf.getvalue(),
        media_type="application/x-protobuf",
        headers={"Content-Encoding": "gzip"}
    )

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/style.json")
def style():
    if not os.path.exists(STYLE_PATH):
        raise HTTPException(500, "style.json missing")
    with open(STYLE_PATH, "r") as f:
        return json.load(f)

@app.get("/tiles/{z}/{x}/{y}.pbf")
def tiles(z: int, x: int, y: int):
    tms_y = (2 ** z - 1) - y
    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        "SELECT tile_data FROM tiles WHERE zoom_level=? AND tile_column=? AND tile_row=?",
        (z, x, tms_y)
    )
    row = cur.fetchone()
    conn.close()

    if row is None:
        raise HTTPException(404, "Tile not found")

    return gzip_if_accepted(row["tile_data"])

@app.get("/sprites/{filename:path}")
def sprites(filename: str):
    return FileResponse(os.path.join(SPRITES_DIR, filename))

@app.get("/fonts/{font_path:path}")
def fonts(font_path: str):
    return FileResponse(os.path.join(FONTS_DIR, font_path))

def start_tile_server():
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)
