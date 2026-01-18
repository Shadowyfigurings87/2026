# host/services/connect/mjpeg_handler.py

from host.logs.wrappers import log_ingest
from host.services.frame_store import save_frame, store_latest_frame

MJPEG_SAVE_EVERY_N = 5

mjpeg_clients = 0
mjpeg_frames_total = 0
mjpeg_bytes_total = 0


def handle_mjpeg_client(conn, addr):
    """
    Handles MJPEG stream from rover camera.
    """
    global mjpeg_clients, mjpeg_frames_total, mjpeg_bytes_total

    mjpeg_clients += 1
    log_ingest("mjpeg_client_connected", addr=str(addr), active=mjpeg_clients)

    frame_counter = 0

    try:
        f = conn.makefile("rb")

        while True:
            boundary = f.readline()
            if not boundary:
                break

            if not boundary.startswith(b"--frame"):
                log_ingest("mjpeg_unexpected_boundary", boundary=boundary[:64])
                continue

            # Read headers
            headers = {}
            while True:
                line = f.readline()
                if not line or line in (b"\r\n", b"\n"):
                    break
                try:
                    key, value = line.decode("utf-8", errors="ignore").split(":", 1)
                    headers[key.strip().lower()] = value.strip()
                except ValueError:
                    continue

            content_length = headers.get("content-length")
            if not content_length:
                log_ingest("mjpeg_missing_content_length", headers=headers)
                break

            try:
                length = int(content_length)
            except ValueError:
                log_ingest("mjpeg_invalid_content_length", value=content_length)
                break

            jpeg_bytes = f.read(length)
            if not jpeg_bytes or len(jpeg_bytes) < length:
                log_ingest(
                    "mjpeg_incomplete_frame",
                    expected=length,
                    got=len(jpeg_bytes or b""),
                )
                break

            # Update counters
            mjpeg_frames_total += 1
            mjpeg_bytes_total += len(jpeg_bytes)
            frame_counter += 1

            # Update latest frame
            store_latest_frame(jpeg_bytes)

            # Save every N frames
            if frame_counter % MJPEG_SAVE_EVERY_N == 0:
                try:
                    path = save_frame(jpeg_bytes)
                    log_ingest(
                        "mjpeg_frame_saved",
                        path=path,
                        size=len(jpeg_bytes),
                        total_frames=mjpeg_frames_total,
                    )
                except Exception as e:
                    log_ingest("mjpeg_frame_save_error", error=str(e))

            # Consume trailing newline
            _ = f.readline()

    except Exception as e:
        log_ingest("mjpeg_client_crashed", error=str(e), addr=str(addr))

    finally:
        mjpeg_clients -= 1
        try:
            conn.close()
        except Exception:
            pass

        log_ingest(
            "mjpeg_client_disconnected",
            addr=str(addr),
            active=mjpeg_clients,
        )
