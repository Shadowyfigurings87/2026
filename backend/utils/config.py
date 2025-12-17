import os
import yaml
from pathlib import Path

CONFIG_PATH = Path(__file__).resolve().parent.parent / "data" / "config.yaml"

with open(CONFIG_PATH, "r") as f:
    CONFIG = yaml.safe_load(f)

def get_db_path():
    db_path = CONFIG["database"]["path"]
    return os.path.abspath(db_path)

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
