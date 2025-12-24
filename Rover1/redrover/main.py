from ministries.camera.cam import camera_stream
from ministries.esp32.esp32 import esp32_stream
from ministries.alfa.alfa1200 import alfa_stream
from transport.tcp_client import send_jsonl_stream

def combined_generator():
    """
    Simple round-robin over different sensor streams.
    Each inner stream is an infinite generator.
    """
    cams = camera_stream()
    esp = esp32_stream()
    alfa = alfa_stream()
    while True:
        yield next(cams)
        yield next(esp)
        yield next(alfa)

def main():
    # Point host/port to Rover1's Ethernet IP + 9100
    send_jsonl_stream(
        generator=combined_generator,
        host="192.168.1.50",  # Rover1 IP on Ethernet
        port=9100,
    )

if __name__ == "__main__":
    main()
