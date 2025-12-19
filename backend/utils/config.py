import os
import yaml
from pathlib import Path

# Resolve the backend root directory (two levels up from this file)
BASE_DIR = Path(__file__).resolve().parent.parent

# Absolute path to the data directory
DATA_DIR = BASE_DIR / "data"

# Absolute path to the SQLite database
DB_PATH = DATA_DIR / "rf_archive.db"

# Absolute path to config.yaml
CONFIG_PATH = DATA_DIR / "config.yaml"

# Load config.yaml
with open(CONFIG_PATH, "r") as f:
    CONFIG = yaml.safe_load(f)

def get_db_path() -> str:
    """
    Always return the absolute path to the sovereign archive.
    """
    return str(DB_PATH)

def get_poll_interval() -> float:
    ms = CONFIG["streaming"]["poll_interval_ms"]
    return ms / 1000.0

def get_server_host() -> str:
    return CONFIG["server"]["host"]

def get_server_port() -> int:
    return CONFIG["server"]["port"]

def get_classification_settings() -> dict:
    return CONFIG.get("classification", {})

def load_config():
    return CONFIG
