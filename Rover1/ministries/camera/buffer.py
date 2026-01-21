import threading

class FrameBuffer:
    def __init__(self, size=3):
        self.size = size
        self.frames = []
        self.lock = threading.Lock()

    def push(self, frame):
        with self.lock:
            self.frames.append(frame)
            if len(self.frames) > self.size:
                self.frames.pop(0)

    def latest(self):
        with self.lock:
            return self.frames[-1] if self.frames else None
