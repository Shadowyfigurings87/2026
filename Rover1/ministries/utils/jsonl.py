import json
import time

def now_ts():
    return time.time()

def encode_jsonl(obj):
    return json.dumps(obj, separators=(",", ":")) + "\n"

def safe_parse(line):
    line = line.strip()
    if not line:
        return None
    try:
        return json.loads(line)
    except json.JSONDecodeError:
        return None
