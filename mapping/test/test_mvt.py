import sqlite3
import tempfile
import os
from shapely.geometry import (
    Point, LineString, Polygon, MultiPolygon
)
import mapbox_vector_tile as mvt
import math
import traceback

print("\n=== TILEGEN FULL COMPATIBILITY TEST SUITE ===\n")

# ------------------------------------------------------------
# Helper: run a test and print result
# ------------------------------------------------------------
def run_test(name, fn):
    print(f"→ {name}")
    try:
        fn()
        print("   ✔ SUCCESS\n")
    except Exception as e:
        print("   ✘ FAILED:", type(e).__name__, "-", str(e))
        traceback.print_exc()
        print()

# ------------------------------------------------------------
# Test 1: Encoder accepts single layer dict
# ------------------------------------------------------------
def test_single_layer():
    feature = {
        "geometry": Point(0, 0).__geo_interface__,
        "properties": {},
        "id": None,
    }
    layer = {"name": "test", "features": [feature]}
    mvt.encode(layer)

# ------------------------------------------------------------
# Test 2: Encoder accepts list of layers
# ------------------------------------------------------------
def test_list_layers():
    feature = {
        "geometry": Point(0, 0).__geo_interface__,
        "properties": {},
        "id": None,
    }
    layers = [
        {"name": "test", "features": [feature]}
    ]
    mvt.encode(layers)

# ------------------------------------------------------------
# Test 3: Encoder rejects dict-of-layers
# ------------------------------------------------------------
def test_dict_layers_rejected():
    feature = {
        "geometry": Point(0, 0).__geo_interface__,
        "properties": {},
        "id": None,
    }
    bad = {
        "test": {"name": "test", "features": [feature]}
    }
    try:
        mvt.encode(bad)
        raise AssertionError("Dict-of-layers should fail but succeeded")
    except KeyError:
        pass  # expected

# ------------------------------------------------------------
# Test 4: Geometry types supported
# ------------------------------------------------------------
def test_geometry_types():
    geoms = [
        Point(1, 1),
        LineString([(0, 0), (1, 1)]),
        Polygon([(0,0),(1,0),(1,1),(0,1),(0,0)]),
        MultiPolygon([
            Polygon([(0,0),(2,0),(2,2),(0,2),(0,0)]),
            Polygon([(3,3),(4,3),(4,4),(3,4),(3,3)])
        ])
    ]

    features = [
        {"geometry": g.__geo_interface__, "properties": {}, "id": None}
        for g in geoms
    ]

    layers = [{"name": "test", "features": features}]
    mvt.encode(layers)

# ------------------------------------------------------------
# Test 5: Polygon with hole
# ------------------------------------------------------------
def test_polygon_with_hole():
    outer = [(0,0),(5,0),(5,5),(0,5),(0,0)]
    inner = [(1,1),(4,1),(4,4),(1,4),(1,1)]
    poly = Polygon(outer, [inner])

    feature = {
        "geometry": poly.__geo_interface__,
        "properties": {},
        "id": None,
    }

    layers = [{"name": "test", "features": [feature]}]
    mvt.encode(layers)

# ------------------------------------------------------------
# Test 6: Empty geometry handling
# ------------------------------------------------------------
def test_empty_geometry():
    poly = Polygon()  # empty
    feature = {
        "geometry": poly.__geo_interface__,
        "properties": {},
        "id": None,
    }
    layers = [{"name": "test", "features": [feature]}]
    mvt.encode(layers)

# ------------------------------------------------------------
# Test 7: Quantize bounds compatibility
# ------------------------------------------------------------
def test_quantize_bounds():
    feature = {
        "geometry": Point(0, 0).__geo_interface__,
        "properties": {},
        "id": None,
    }
    layers = [{"name": "test", "features": [feature]}]

    mvt.encode(
        layers,
        quantize_bounds=(-180, -85, 180, 85)
    )

# ------------------------------------------------------------
# Test 8: Tile math sanity
# ------------------------------------------------------------
def test_tile_math():
    def lonlat_to_tile(lon, lat, z):
        n = 2 ** z
        xtile = int((lon + 180.0) / 360.0 * n)
        ytile = int(
            (1.0 - math.log(math.tan(math.radians(lat)) + 1 / math.cos(math.radians(lat))) / math.pi)
            / 2.0 * n
        )
        return xtile, ytile

    x, y = lonlat_to_tile(-81.7, 30.3, 10)
    assert 0 <= x < 2**10
    assert 0 <= y < 2**10

# ------------------------------------------------------------
# Test 9: MBTiles write path
# ------------------------------------------------------------
def test_mbtiles_write():
    tmp = tempfile.NamedTemporaryFile(delete=False)
    tmp.close()
    path = tmp.name

    conn = sqlite3.connect(path)
    cur = conn.cursor()

    cur.execute("CREATE TABLE tiles (zoom_level INTEGER, tile_column INTEGER, tile_row INTEGER, tile_data BLOB)")
    conn.commit()

    feature = {
        "geometry": Point(0, 0).__geo_interface__,
        "properties": {},
        "id": None,
    }
    layers = [{"name": "test", "features": [feature]}]
    tile_data = mvt.encode(layers)

    cur.execute(
        "INSERT INTO tiles VALUES (?, ?, ?, ?)",
        (0, 0, 0, sqlite3.Binary(tile_data))
    )
    conn.commit()
    conn.close()

    os.unlink(path)

# ------------------------------------------------------------
# Test 10: Checkpoint table logic
# ------------------------------------------------------------
def test_checkpoints():
    tmp = tempfile.NamedTemporaryFile(delete=False)
    tmp.close()
    path = tmp.name

    conn = sqlite3.connect(path)
    cur = conn.cursor()

    cur.execute("CREATE TABLE checkpoints (zoom_level INTEGER PRIMARY KEY, done INTEGER)")
    conn.commit()

    cur.execute("INSERT INTO checkpoints VALUES (?, ?)", (0, 1))
    conn.commit()

    row = cur.execute("SELECT done FROM checkpoints WHERE zoom_level = 0").fetchone()
    assert row[0] == 1

    conn.close()
    os.unlink(path)

# ------------------------------------------------------------
# Run all tests
# ------------------------------------------------------------

tests = [
    ("Encoder: single layer dict", test_single_layer),
    ("Encoder: list of layers", test_list_layers),
    ("Encoder: dict-of-layers rejected", test_dict_layers_rejected),
    ("Geometry types", test_geometry_types),
    ("Polygon with hole", test_polygon_with_hole),
    ("Empty geometry", test_empty_geometry),
    ("Quantize bounds", test_quantize_bounds),
    ("Tile math", test_tile_math),
    ("MBTiles write path", test_mbtiles_write),
    ("Checkpoint logic", test_checkpoints),
]

for name, fn in tests:
    run_test(name, fn)

print("\n=== ALL TESTS COMPLETE ===\n")
