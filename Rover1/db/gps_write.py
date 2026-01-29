import os, sqlite3

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(BASE_DIR, ".."))
DB_PATH = os.path.join(PROJECT_ROOT, "data", "gps.db")

os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

def write_gps(ts, lat, lon):
    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO gps (ts, lat, lon) VALUES (?, ?, ?)",
            (ts, lat, lon)
        )
        conn.commit()
        conn.close()
        print("[GPS Write] OK")
    except Exception as e:
        print(f"[GPS Write] Error writing GPS row: {e}")
