# services/channel_model.py

import time
import threading
import numpy as np
from collections import defaultdict, deque

from backend.utils.logging_config import log_event

PROFILE_WINDOW = 2000      # frames per channel to keep
MIN_PROFILE_SIZE = 100     # minimum frames before scoring


class ChannelModel:
    def __init__(self):
        # Per-channel rolling buffers
        self.rssi = defaultdict(lambda: deque(maxlen=PROFILE_WINDOW))
        self.signal_quality = defaultdict(lambda: deque(maxlen=PROFILE_WINDOW))
        self.activity = defaultdict(lambda: deque(maxlen=PROFILE_WINDOW))
        self.frame_types = defaultdict(lambda: deque(maxlen=PROFILE_WINDOW))
        self.utilization = defaultdict(lambda: deque(maxlen=PROFILE_WINDOW))

        self.lock = threading.Lock()

        log_event("channel_model", "INFO", "engine_initialized", {})

    # -----------------------------
    # Public API
    # -----------------------------
    def update_and_score(self, frame: dict):
        """
        Update channel profile and return a deviation score (0–1).
        Higher = more abnormal.
        """
        ch = frame.get("channel")
        if ch is None:
            return None

        rssi = frame.get("rssi")
        sq = frame.get("signal_quality")
        act = frame.get("activity_score")
        ft = frame.get("frame_type")

        with self.lock:
            # Update rolling buffers
            if rssi is not None:
                self.rssi[ch].append(rssi)
            if sq is not None:
                self.signal_quality[ch].append(sq)
            if act is not None:
                self.activity[ch].append(act)
            if ft is not None:
                self.frame_types[ch].append(ft)

            # Utilization = frame count per window
            self.utilization[ch].append(1)

            # Not enough data yet
            if len(self.rssi[ch]) < MIN_PROFILE_SIZE:
                return None

            # Compute deviation
            return float(self._compute_deviation(ch, frame))

    # -----------------------------
    # Internal: deviation scoring
    # -----------------------------
    def _compute_deviation(self, ch, frame):
        """
        Compute how different this frame is from the channel's baseline.
        Returns a score in [0, 1].
        """

        # Baselines
        rssi_mean = np.mean(self.rssi[ch])
        sq_mean = np.mean(self.signal_quality[ch]) if self.signal_quality[ch] else 0
        act_mean = np.mean(self.activity[ch]) if self.activity[ch] else 0
        util_mean = np.mean(self.utilization[ch])  # frames per sample

        # Current values
        rssi = frame.get("rssi") or 0
        sq = frame.get("signal_quality") or 0
        act = frame.get("activity_score") or 0

        # Deviations (normalized)
        rssi_dev = abs(rssi - rssi_mean) / 50.0
        sq_dev = abs(sq - sq_mean) / 50.0
        act_dev = abs(act - act_mean) / 50.0

        # Utilization deviation (detects jamming / flooding)
        util_dev = 0
        if util_mean > 0:
            util_dev = abs(1 - util_mean)  # crude but effective

        # Frame type deviation
        ft = frame.get("frame_type")
        ft_dev = 0
        if ft is not None:
            ft_dev = 0 if ft in self.frame_types[ch] else 1

        # Combine
        score = (
            0.35 * rssi_dev +
            0.20 * sq_dev +
            0.20 * act_dev +
            0.15 * util_dev +
            0.10 * ft_dev
        )

        # Clamp
        if score < 0:
            score = 0
        if score > 1:
            score = 1

        return score


# Singleton instance
engine = ChannelModel()
