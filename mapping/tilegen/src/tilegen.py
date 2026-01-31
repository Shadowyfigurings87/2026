import sqlite3
from pathlib import Path
from shapely.geometry import shape, Polygon
import mapbox_vector_tile as mvt
import math
import ijson
import time

# --------------------------------------------------------------------
# CONFIG
# --------------------------------------------------------------------

DATA = {
    "roads": "/home/zachariah/2026/mapping/tilegen/data/roads.geojson",
    "buildings": "/home/zachariah/2026/mapping/tilegen/data/buildings.geojson",
    "water": "/home/zachariah/2026/mapping/tilegen/data/water.geojson",
}

OUT = "/home/zachariah/2026/mapping/tilegen/output/florida.mbtiles"

MIN_Z = 0
MAX_Z = 18

TILE_BATCH_LIMIT = 5000

BOUNDS = (-88.0, 24.0, -79.0, 32.0)

METADATA = {
    "name": "Florida Sovereign Tiles",
    "description": "Sovereign vector tiles for Florida (roads, buildings, water).",
    "format": "pbf",
    "version": "1",
    "minzoom": str(MIN_Z),
    "maxzoom": str(MAX_Z),
    "bounds": ",".join(str(v) for v in BOUNDS),
    "center": "-81.7,30.3,10",
}

# --------------------------------------------------------------------
# LOGGING
# --------------------------------------------------------------------

def log(msg):
    print(f"[tilegen] {msg}", flush=True)

# --------------------------------------------------------------------
# ENCODER SELF-CHECK (BASED ON OUR KNOWNS)
# --------------------------------------------------------------------

def verify_encoder_contract():
    """
    Verify that mapbox_vector_tile.encode behaves as expected:

    - accepts single layer dict
    - accepts list of layer dicts
    - rejects dict-of-layers with KeyError('name')
    """
    from shapely.geometry import Point

    fake_geom = Point(0, 0).__geo_interface__
    feature = {"geometry": fake_geom, "properties": {}, "id": None}

    single_layer = {"name": "test", "features": [feature]}
    list_layers = [{"name": "test", "features": [feature]}]
    dict_layers = {"test": {"name": "test", "features": [feature]}}

    # single layer dict must succeed
    mvt.encode(single_layer)

    # list of layers must succeed
    mvt.encode(list_layers)

    # dict-of-layers must fail with KeyError
    try:
        mvt.encode(dict_layers)
    except KeyError:
        return
    raise RuntimeError(
        "mapbox_vector_tile.encode no longer rejects dict-of-layers; "
        "tilegen assumptions need to be revisited."
    )

# --------------------------------------------------------------------
# TILE MATH
# --------------------------------------------------------------------

def lonlat_to_tile(lon, lat, z):
    n = 2 ** z
    xtile = int((lon + 180.0) / 360.0 * n)
    ytile = int(
        (1.0 - math.log(math.tan(math.radians(lat)) + 1 / math.cos(math.radians(lat))) / math.pi)
        / 2.0 * n
    )
    return xtile, ytile

def tile_bounds(x, y, z):
    n = 2 ** z
    lon_min = x / n * 360.0 - 180.0
    lon_max = (x + 1) / n * 360.0 - 180.0

    def lat_from_y(ty):
        n2 = math.pi - 2.0 * math.pi * ty / n
        return math.degrees(math.atan(math.sinh(n2)))

    lat_max = lat_from_y(y)
    lat_min = lat_from_y(y + 1)
    return lon_min, lat_min, lon_max, lat_max

# --------------------------------------------------------------------
# MBTILES + CHECKPOINTS
# --------------------------------------------------------------------

def init_mbtiles(path):
    new_file = not Path(path).exists()
    conn = sqlite3.connect(path)
    cur = conn.cursor()

    if new_file:
        log("No existing MBTiles found, creating new file...")
        cur.execute("CREATE TABLE tiles (zoom_level INTEGER, tile_column INTEGER, tile_row INTEGER, tile_data BLOB)")
        cur.execute("CREATE TABLE metadata (name TEXT, value TEXT)")
        cur.execute("CREATE TABLE checkpoints (zoom_level INTEGER PRIMARY KEY, done INTEGER)")

        for k, v in METADATA.items():
            cur.execute("INSERT INTO metadata (name, value) VALUES (?, ?)", (k, v))

        conn.commit()
    else:
        log("Existing MBTiles found, opening for resume...")
        cur.execute("CREATE TABLE IF NOT EXISTS checkpoints (zoom_level INTEGER PRIMARY KEY, done INTEGER)")
        conn.commit()

    return conn

def zoom_done(cur, z):
    row = cur.execute("SELECT done FROM checkpoints WHERE zoom_level = ?", (z,)).fetchone()
    return row is not None and row[0] == 1

def mark_zoom_done(cur, z):
    cur.execute("INSERT OR REPLACE INTO checkpoints (zoom_level, done) VALUES (?, 1)", (z,))

# --------------------------------------------------------------------
# GEOJSON STREAMING
# --------------------------------------------------------------------

def iter_features(path):
    with open(path, "rb") as f:
        for feat in ijson.items(f, "features.item"):
            if "geometry" not in feat or feat["geometry"] is None:
                continue
            try:
                geom = shape(feat["geometry"])
            except Exception:
                continue
            # Skip geometry collections at source level
            if geom.geom_type == "GeometryCollection":
                continue
            yield geom

# --------------------------------------------------------------------
# GEOMETRY FILTERING
# --------------------------------------------------------------------

def maybe_simplify_and_filter(geom, z, layer_name):
    if geom.is_empty or not geom.bounds:
        return None

    # Skip geometry collections anywhere they sneak in
    if geom.geom_type == "GeometryCollection":
        return None

    if z < 13 and layer_name == "buildings":
        if geom.area < 1e-6:
            return None

    if z < 13:
        try:
            geom = geom.simplify(0.0001, preserve_topology=True)
        except Exception:
            pass
        if geom.is_empty:
            return None

    # If simplification produced a GeometryCollection, drop it
    if geom.geom_type == "GeometryCollection":
        return None

    return geom

# --------------------------------------------------------------------
# TILE FLUSHING (LIST-OF-LAYERS FORMAT)
# --------------------------------------------------------------------

def flush_tiles(cur, z, tiles):
    if not tiles:
        return

    log(f"    Flushing {len(tiles)} tiles for zoom {z}")

    for (x, y), layer_dict in tiles.items():
        layers_list = []
        for lname, layer in layer_dict.items():
            # Filter out any features whose geometry is a GeometryCollection
            clean_features = []
            for feat in layer["features"]:
                geom = feat.get("geometry")
                # geom is a __geo_interface__ dict; check its "type"
                if not geom or geom.get("type") == "GeometryCollection":
                    continue
                clean_features.append(feat)

            if not clean_features:
                continue

            layers_list.append({
                "name": lname,
                "features": clean_features,
            })

        if not layers_list:
            continue

        lon_min, lat_min, lon_max, lat_max = tile_bounds(x, y, z)

        tile_data = mvt.encode(
            layers_list,
            quantize_bounds=(lon_min, lat_min, lon_max, lat_max),
        )

        tms_y = (2 ** z - 1) - y

        cur.execute(
            "INSERT INTO tiles VALUES (?, ?, ?, ?)",
            (z, x, tms_y, sqlite3.Binary(tile_data)),
        )

    tiles.clear()

# --------------------------------------------------------------------
# MAIN
# --------------------------------------------------------------------

def main():
    log("Verifying encoder contract...")
    verify_encoder_contract()
    log("Encoder contract verified.")

    log("Initializing MBTiles (with checkpoints)...")
    conn = init_mbtiles(OUT)
    cur = conn.cursor()
    log("MBTiles ready.")

    for z in range(MIN_Z, MAX_Z + 1):
        if zoom_done(cur, z):
            log(f"=== Zoom {z} already complete — skipping ===")
            continue

        zoom_start = time.time()
        log(f"=== Zoom {z} starting ===")
        tiles = {}

        for lname, path in DATA.items():
            log(f"  → Layer {lname} streaming...")
            feat_count = 0

            for geom in iter_features(path):
                feat_count += 1
                if feat_count % 5000 == 0:
                    log(f"    {lname}: streamed {feat_count:,} features...")

                geom = maybe_simplify_and_filter(geom, z, lname)
                if geom is None:
                    continue

                # Final guard: never let GeometryCollection through
                if geom.geom_type == "GeometryCollection":
                    continue

                minx, miny, maxx, maxy = geom.bounds

                miny = max(miny, -85.05112878)
                maxy = min(maxy, 85.05112878)
                minx = max(minx, -180.0)
                maxx = min(maxx, 180.0)

                tx_min, ty_max = lonlat_to_tile(minx, miny, z)
                tx_max, ty_min = lonlat_to_tile(maxx, maxy, z)

                if tx_min > tx_max:
                    tx_min, tx_max = tx_max, tx_min
                if ty_min > ty_max:
                    ty_min, ty_max = ty_max, ty_min

                for tx in range(tx_min, tx_max + 1):
                    for ty in range(ty_min, ty_max + 1):
                        lon_min, lat_min, lon_max, lat_max = tile_bounds(tx, ty, z)
                        bbox = Polygon([
                            (lon_min, lat_min),
                            (lon_max, lat_min),
                            (lon_max, lat_max),
                            (lon_min, lat_max),
                        ])

                        try:
                            clipped = geom.intersection(bbox)
                        except Exception:
                            continue

                        if clipped.is_empty:
                            continue

                        # Guard again after clipping
                        if clipped.geom_type == "GeometryCollection":
                            continue

                        key = (tx, ty)
                        if key not in tiles:
                            tiles[key] = {}
                        if lname not in tiles[key]:
                            tiles[key][lname] = {"features": []}

                        tiles[key][lname]["features"].append({
                            "geometry": clipped.__geo_interface__,
                            "properties": {},
                            "id": None,
                        })

                        if len(tiles) >= TILE_BATCH_LIMIT:
                            flush_tiles(cur, z, tiles)

            log(f"  ← Layer {lname} complete ({feat_count:,} features processed)")

        flush_tiles(cur, z, tiles)

        mark_zoom_done(cur, z)
        conn.commit()

        zoom_time = time.time() - zoom_start
        log(f"=== Zoom {z} complete in {zoom_time:.1f}s ===")

    conn.close()
    log("All zooms complete. Done.")

if __name__ == "__main__":
    main()
