import json
import time

def now_ts():
    return time.time()

def encode_jsonl(obj):
    return json.dumps(obj, separators=(",", ":")) + "\n"
