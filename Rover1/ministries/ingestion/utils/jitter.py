# ingestion/utils/jitter.py

from collections import deque

class JitterSmoother:
    def __init__(self, window_size=10, max_spike_factor=3.0):
        self.window = deque(maxlen=window_size)
        self.last_ts = None
        self.max_spike_factor = max_spike_factor

    def smooth(self, ts):
        if self.last_ts is None:
            self.last_ts = ts
            return ts

        delta = ts - self.last_ts
        if delta <= 0:
            ts = self.last_ts + 0.001
            self.last_ts = ts
            return ts

        if self.window:
            avg_delta = sum(self.window) / len(self.window)
            if delta > avg_delta * self.max_spike_factor:
                delta = avg_delta
                ts = self.last_ts + delta

        self.window.append(delta)
        self.last_ts = ts
        return ts
