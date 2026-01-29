import os, sqlite3

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(BASE_DIR, ".."))
DB_PATH = os.path.join(PROJECT_ROOT, "data", "gps.db")

def get_latest_gps():
    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("SELECT ts, lat, lon FROM gps ORDER BY id DESC LIMIT 1")
        row = cur.fetchone()
        conn.close()
        return row
    except Exception as e:
        print(f"[GPS Query] Error reading latest GPS row: {e}")
        return None
