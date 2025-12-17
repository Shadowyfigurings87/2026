# tools/replay_jsonl.py

import json
import argparse
from pathlib import Path
import db


def insert_frame(rec: dict):
    sql = """
        INSERT INTO frames (
            timestamp, source, iface,
            frame_type, subtype, direction,
            src_mac, dst_mac, bssid, ssid,
            channel, rssi, rate, channel_freq, channel_flags,
            summary,
            src_role, dst_role, bssid_role,
            sensor_id, sensor_component_role,
            rssi_normalized, signal_quality, activity_score
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """

    params = (
        rec.get("timestamp"),
        rec.get("source"),
        rec.get("iface"),
        rec.get("frame_type"),
        rec.get("subtype"),
        rec.get("direction"),
        rec.get("src_mac"),
        rec.get("dst_mac"),
        rec.get("bssid"),
        rec.get("ssid"),
        rec.get("channel"),
        rec.get("rssi"),
        rec.get("rate"),
        rec.get("channel_freq"),
        rec.get("channel_flags"),
        rec.get("summary"),
        rec.get("src_role"),
        rec.get("dst_role"),
        rec.get("bssid_role"),
        rec.get("sensor_id"),
        rec.get("sensor_component_role"),
        rec.get("rssi_normalized"),
        rec.get("signal_quality"),
        rec.get("activity_score"),
    )

    db.execute(sql, params)


def main():
    parser = argparse.ArgumentParser(description="Replay frames JSONL into rf_archive.db")
    parser.add_argument("jsonl_path", help="Path to frames JSONL file")
    parser.add_argument("--limit", type=int, default=None)
    args = parser.parse_args()

    path = Path(args.jsonl_path)
    if not path.exists():
        raise SystemExit(f"File not found: {path}")

    count = 0
    with path.open("r") as f:
        for line in f:
            if args.limit is not None and count >= args.limit:
                break
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            insert_frame(rec)
            count += 1

    print(f"[+] Inserted {count} frames into frames table.")


if __name__ == "__main__":
    main()
