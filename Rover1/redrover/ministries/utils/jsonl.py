import json

def encode_jsonl(obj):
    return json.dumps(obj, separators=(",", ":")) + "\n"

