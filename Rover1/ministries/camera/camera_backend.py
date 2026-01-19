from picamera2 import Picamera2
import threading

_picam = None
_lock = threading.Lock()

def get_camera():
    global _picam
    with _lock:
        if _picam is None:
            _picam = Picamera2()
            config = _picam.create_video_configuration(main={"size": (640, 480)})
            _picam.configure(config)
            _picam.start()
        return _picam
