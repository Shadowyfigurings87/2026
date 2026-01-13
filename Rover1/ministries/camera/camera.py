import socket
import threading
import time
from picamera2 import Picamera2
import io

class MJPEGStreamer:
    def __init__(self, host, port, fps=10):
        self.host = host
        self.port = port
        self.fps = fps
        self.running = False
        self.thread = None

        # Initialize camera
        self.picam = Picamera2()
        config = self.picam.create_video_configuration(main={"size": (640, 480)})
        self.picam.configure(config)
        self.picam.start()

        self.frame_delay = 1.0 / fps

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
            sock = None
            conn = None

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
                    content_length = str(len(jpeg_bytes)).encode()

                    # Write MJPEG frame (Content-Length compliant)
                    conn.write(b"--frame\r\n")
                    conn.write(b"Content-Type: image/jpeg\r\n")
                    conn.write(b"Content-Length: " + content_length + b"\r\n")
                    conn.write(b"\r\n")
                    conn.write(jpeg_bytes)
                    conn.write(b"\r\n")
                    conn.flush()

                    time.sleep(self.frame_delay)

            except Exception:
                # Retry after short delay
                time.sleep(1)

            finally:
                try:
                    if conn:
                        conn.close()
                except:
                    pass
                try:
                    if sock:
                        sock.close()
                except:
                    pass
