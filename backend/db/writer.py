import sqlite3
import time
from queue import Empty
from utils.logging import log_event
import threading

BATCH_SIZE = 100
BATCH_TIMEOUT = 0.25


def db_writer_thread(db_path, ingest_queue):
    conn = sqlite3.connect(db_path, isolation_level=None)
    cursor = conn.cursor()

    log_event("db_writer", "INFO", "writer_online")

    batch = []
    last_commit = time.time()

    while True:
        try:
            frame = ingest_queue.get(timeout=BATCH_TIMEOUT)
            batch.append(frame)
        except Empty:
            pass

        # Flush if batch is full or timeout expired
        if len(batch) >= BATCH_SIZE or (batch and time.time() - last_commit >= BATCH_TIMEOUT):
            try:
                # Debug log before attempting insert
                log_event("db_writer", "DEBUG", "flush_attempt", {
                    "batch_size": len(batch),
                    "elapsed": round(time.time() - last_commit, 3)
                })

                # Build safe batch with defaults for missing fields
                safe_batch = []
                for f in batch:
                    safe_batch.append({
                        "timestamp": f.get("timestamp"),
                        "source": f.get("source"),
                        "iface": f.get("iface"),
                        "frame_type": f.get("frame_type"),
                        "subtype": f.get("subtype"),
                        "direction": f.get("direction"),
                        "src": f.get("src"),
                        "dst": f.get("dst"),
                        "bssid": f.get("bssid"),
                        "ssid": f.get("ssid"),
                        "channel": f.get("channel"),
                        "rssi": f.get("rssi"),
                        "rate": f.get("rate"),
                        "channel_freq": f.get("channel_freq"),
                        "channel_flags": f.get("channel_flags"),
                        "summary": f.get("summary"),

                        # Safe defaults for missing enriched fields
                        "src_role": f.get("src_role"),
                        "dst_role": f.get("dst_role"),
                        "bssid_role": f.get("bssid_role"),
                        "sensor_id": f.get("sensor_id"),
                        "sensor_component_role": f.get("sensor_component_role"),
                        "rssi_normalized": f.get("rssi_normalized"),
                        "signal_quality": f.get("signal_quality"),
                        "activity_score": f.get("activity_score"),
                    })

                cursor.executemany(
                    """
                    INSERT INTO frames (
                        timestamp, source, iface,
                        frame_type, subtype, direction,
                        src_mac, dst_mac, bssid, ssid,
                        channel, rssi, rate, channel_freq, channel_flags,
                        summary,
                        src_role, dst_role, bssid_role,
                        sensor_id, sensor_component_role,
                        rssi_normalized, signal_quality, activity_score
                    ) VALUES (
                        :timestamp, :source, :iface,
                        :frame_type, :subtype, :direction,
                        :src, :dst, :bssid, :ssid,
                        :channel, :rssi, :rate, :channel_freq, :channel_flags,
                        :summary,
                        :src_role, :dst_role, :bssid_role,
                        :sensor_id, :sensor_component_role,
                        :rssi_normalized, :signal_quality, :activity_score
                    )
                    """,
                    safe_batch
                )
                conn.commit()

                # Log AFTER successful commit, BEFORE clearing
                log_event("db_writer", "INFO", "batch_insert", {"count": len(batch)})

                batch.clear()
                last_commit = time.time()

            except Exception as e:
                conn.rollback()
                log_event("db_writer", "ERROR", "batch_insert_failed", {"error": str(e)})


def start_db_writer(db_path, ingest_queue):
    t = threading.Thread(
        target=db_writer_thread,
        args=(db_path, ingest_queue),
        daemon=True
    )
    t.start()
