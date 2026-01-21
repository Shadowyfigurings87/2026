# ingestion/utils/ministry.py

def ensure_ministry(obj, default):
    if "ministry" not in obj or obj["ministry"] is None:
        obj["ministry"] = default
    return obj
