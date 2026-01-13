import socket
import threading
import time
from picamera2 import Picamera2
import io

MJPEG_BOUNDARY = b"--frame\r\n"
MJPEG_HEADER = b"Content-Type: image/jpeg\r\n\r\n"

class MJPEGStreamer:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.running = False
        self.thread = None

        # Initialize camera
        self.picam = Picamera2()
        config = self.picam.create_video_configuration(main={"size": (640, 480)})
        self.picam.configure(config)
        self.picam.start()

    def start(self):
        if self.running:
            return
        self.running = True
        self.thread = threading.Thread(target=self._stream_loop, daemon=True)
        self.thread.start()

    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join()

    def _stream_loop(self):
        while self.running:
            try:
                # Connect to host
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.connect((self.host, self.port))
                conn = sock.makefile("wb")

                while self.running:
                    # Capture JPEG frame
                    buffer = io.BytesIO()
                    self.picam.capture_file(buffer, format="jpeg")
                    jpeg_bytes = buffer.getvalue()

                    # Write MJPEG frame
                    conn.write(MJPEG_BOUNDARY)
                    conn.write(MJPEG_HEADER)
                    conn.write(jpeg_bytes)
                    conn.write(b"\r\n")
                    conn.flush()

                    # Control frame rate
                    time.sleep(0.1)  # ~10 FPS

            except Exception as e:
                # If connection fails, retry after short delay
                time.sleep(1)

            finally:
                try:
                    conn.close()
                except:
                    pass
                try:
                    sock.close()
                except:
                    pass
