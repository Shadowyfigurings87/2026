from ministries.camera.cam import camera_stream
from ministries.esp32.esp32 import esp32_stream
from ministries.alfa.alfa1200 import alfa_stream
from transport.tcp_client import send_jsonl_stream

def combined_generator():
    """
    Robust round‑robin generator that merges:
      - camera_stream()
      - esp32_stream()
      - alfa_stream()

    Each ministry is an infinite generator.
    If any ministry fails, we yield an error packet but continue running.
    """

    from ministries.camera.cam import camera_stream
    from ministries.esp32.esp32 import esp32_stream
    from ministries.alfa.alfa1200 import alfa_stream

    streams = {
        "camera": camera_stream(),
        "esp32": esp32_stream(),
        "alfa": alfa_stream(),
    }

    while True:
        for name, gen in streams.items():
            try:
                packet = next(gen)

                # Ensure source tagging
                if "source" not in packet:
                    packet["source"] = name

                yield packet

            except StopIteration:
                # Should never happen for infinite streams
                continue

            except Exception as e:
                # Never kill the pipeline — report error and continue
                yield {
                    "kind": "telemetry",
                    "source": name,
                    "rover": "RedRover",
                    "ts": now_ts(),
                    "error": str(e),
                }

def main():
    # Point host/port to Rover1's Ethernet IP + 9100
    send_jsonl_stream(
        generator=combined_generator,
        host="192.168.1.50",  # Rover1 IP on Ethernet
        port=9100,
    )

if __name__ == "__main__":
    main()
