#!/usr/bin/env python3
import os
import sqlite3
import json
import logging
import gzip
from io import BytesIO
from flask import Flask, send_from_directory, request, Response, abort, make_response

# --------------------------------------------------------------------
# Configuration
# --------------------------------------------------------------------

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(BASE_DIR))

MBTILES_PATH = os.path.join(PROJECT_ROOT, "tilegen", "output", "florida.mbtiles")
STYLE_PATH = os.path.join(PROJECT_ROOT, "map", "style.json")
SPRITES_DIR = os.path.join(PROJECT_ROOT, "sprites")
FONTS_DIR = os.path.join(PROJECT_ROOT, "map", "fonts")

TILE_CONTENT_TYPE = "application/x-protobuf"
STYLE_CONTENT_TYPE = "application/json"

# --------------------------------------------------------------------
# Logging
# --------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] %(message)s",
)
logger = logging.getLogger("sovereign-map-server")

# --------------------------------------------------------------------
# Flask app
# --------------------------------------------------------------------

app = Flask(__name__)

# --------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------

def get_db_connection():
    if not os.path.exists(MBTILES_PATH):
        logger.error(f"MBTiles file not found at {MBTILES_PATH}")
        abort(500, description="MBTiles file not found")
    conn = sqlite3.connect(MBTILES_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def fetch_tile(z, x, y):
    """
    MBTiles uses TMS (y flipped). MapLibre uses XYZ.
    Convert XYZ -> TMS: tms_y = (2^z - 1) - y
    """
    try:
        z = int(z)
        x = int(x)
        y = int(y)
    except ValueError:
        abort(400, description="Invalid tile coordinates")

    tms_y = (2 ** z - 1) - y

    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT tile_data FROM tiles WHERE zoom_level = ? AND tile_column = ? AND tile_row = ?",
            (z, x, tms_y),
        )
        row = cur.fetchone()
    finally:
        conn.close()

    if row is None:
        abort(404, description="Tile not found")

    return bytes(row["tile_data"])


def maybe_gzip(data: bytes, content_type: str) -> Response:
    accept_encoding = request.headers.get("Accept-Encoding", "")
    if "gzip" in accept_encoding.lower():
        buf = BytesIO()
        with gzip.GzipFile(fileobj=buf, mode="wb") as f:
            f.write(data)
        gzipped = buf.getvalue()
        resp = make_response(gzipped)
        resp.headers["Content-Encoding"] = "gzip"
        resp.headers["Content-Type"] = content_type
        resp.headers["Vary"] = "Accept-Encoding"
        return resp
    else:
        resp = make_response(data)
        resp.headers["Content-Type"] = content_type
        return resp


def add_cors(resp: Response) -> Response:
    resp.headers["Access-Control-Allow-Origin"] = "*"
    resp.headers["Access-Control-Allow-Methods"] = "GET, OPTIONS"
    resp.headers["Access-Control-Allow-Headers"] = "Origin, X-Requested-With, Content-Type, Accept"
    return resp


@app.after_request
def after_request(response):
    return add_cors(response)

# --------------------------------------------------------------------
# Routes
# --------------------------------------------------------------------

@app.route("/health")
def health():
    return {"status": "ok"}, 200


@app.route("/style.json")
def style():
    if not os.path.exists(STYLE_PATH):
        abort(500, description="style.json not found")

    with open(STYLE_PATH, "r", encoding="utf-8") as f:
        data = f.read()

    # Optionally validate JSON
    try:
        json.loads(data)
    except json.JSONDecodeError as e:
        logger.error(f"Invalid style.json: {e}")
        abort(500, description="Invalid style.json")

    return maybe_gzip(data.encode("utf-8"), STYLE_CONTENT_TYPE)


@app.route("/tiles/<int:z>/<int:x>/<int:y>.pbf")
def tiles(z, x, y):
    logger.info(f"Tile request z={z} x={x} y={y}")
    tile_data = fetch_tile(z, x, y)
    return maybe_gzip(tile_data, TILE_CONTENT_TYPE)


@app.route("/sprites/<path:filename>")
def sprites(filename):
    # Expect sprite.png, sprite.json, sprite@2x.png, sprite@2x.json, etc.
    if not os.path.exists(SPRITES_DIR):
        abort(404, description="Sprites directory not found")
    return send_from_directory(SPRITES_DIR, filename)


@app.route("/fonts/<path:font_path>")
def fonts(font_path):
    # MapLibre requests fonts like: /fonts/{fontstack}/{range}.pbf
    full_path = os.path.join(FONTS_DIR, font_path)
    directory = os.path.dirname(full_path)
    filename = os.path.basename(full_path)

    if not os.path.exists(directory):
        abort(404, description="Font directory not found")

    return send_from_directory(directory, filename)


@app.route("/")
def index():
    return (
        "<h1>Sovereign Map Server</h1>"
        "<p>Endpoints:</p>"
        "<ul>"
        "<li>/style.json</li>"
        "<li>/tiles/{z}/{x}/{y}.pbf</li>"
        "<li>/sprites/sprite.png, sprite.json, ...</li>"
        "<li>/fonts/{fontstack}/{range}.pbf</li>"
        "<li>/health</li>"
        "</ul>"
    )

# --------------------------------------------------------------------
# Main
# --------------------------------------------------------------------

if __name__ == "__main__":
    host = os.environ.get("MAP_SERVER_HOST", "0.0.0.0")
    port = int(os.environ.get("MAP_SERVER_PORT", "8080"))
    logger.info(f"Starting Sovereign Map Server on {host}:{port}")
    logger.info(f"Using MBTiles: {MBTILES_PATH}")
    app.run(host=host, port=port, debug=False)
