# host/services/camera/frame_buffer.py

import threading

class FrameBuffer:
    def __init__(self, max_frames=3):
        self.max_frames = max_frames
        self.frames = []
        self.lock = threading.Lock()

    def push(self, jpeg_bytes):
        with self.lock:
            self.frames.append(jpeg_bytes)
            if len(self.frames) > self.max_frames:
                self.frames.pop(0)

    def latest(self):
        with self.lock:
            return self.frames[-1] if self.frames else None
