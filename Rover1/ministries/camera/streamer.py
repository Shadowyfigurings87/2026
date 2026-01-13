import socket
import threading
import time
import io
from picamera2 import Picamera2


class MJPEGStreamer:
    """
    Sends MJPEG frames directly to the host ingestion server.
    This ministry is independent from the JSON uplink.
    """

    def __init__(self, host, port, fps=10):
        self.host = host
        self.port = port
        self.fps = fps
        self.frame_delay = 1.0 / fps

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
        self.thread = threading.Thread(target=self._loop, daemon=True)
        self.thread.start()

    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join()

    def _loop(self):
        """
        Persistent connection loop.
        Reconnects automatically if the host drops the connection.
        """
        while self.running:
            sock = None
            conn = None

            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.connect((self.host, self.port))
                conn = sock.makefile("wb")

                while self.running:
                    # Capture JPEG
                    buf = io.BytesIO()
                    self.picam.capture_file(buf, format="jpeg")
                    jpeg = buf.getvalue()
                    length = str(len(jpeg)).encode()

                    # MJPEG frame
                    conn.write(b"--frame\r\n")
                    conn.write(b"Content-Type: image/jpeg\r\n")
                    conn.write(b"Content-Length: " + length + b"\r\n\r\n")
                    conn.write(jpeg)
                    conn.write(b"\r\n")
                    conn.flush()

                    time.sleep(self.frame_delay)

            except Exception:
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
