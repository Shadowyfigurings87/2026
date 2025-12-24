# services/device_model.py

import time
import threading
import numpy as np
from collections import defaultdict, deque

from utils.logging_config import log_event

PROFILE_WINDOW = 500      # frames per device to keep
MIN_PROFILE_SIZE = 50     # minimum frames before scoring
DECAY = 0.98              # exponential decay for rolling stats


class DeviceModel:
    def __init__(self):
        # Per-device rolling buffers
        self.rssi = defaultdict(lambda: deque(maxlen=PROFILE_WINDOW))
        self.signal_quality = defaultdict(lambda: deque(maxlen=PROFILE_WINDOW))
        self.activity = defaultdict(lambda: deque(maxlen=PROFILE_WINDOW))
        self.channels = defaultdict(lambda: deque(maxlen=PROFILE_WINDOW))
        self.frame_types = defaultdict(lambda: deque(maxlen=PROFILE_WINDOW))

        self.lock = threading.Lock()

        log_event("device_model", "INFO", "engine_initialized", {})

    # -----------------------------
    # Public API
    # -----------------------------
    def update_and_score(self, frame: dict):
        """
        Update device profile and return a deviation score (0–1).
        Higher = more abnormal.
        """
        mac = frame.get("src")
        if mac is None:
            return None

        rssi = frame.get("rssi")
        sq = frame.get("signal_quality")
        act = frame.get("activity_score")
        ch = frame.get("channel")
        ft = frame.get("frame_type")

        with self.lock:
            # Update rolling buffers
            if rssi is not None:
                self.rssi[mac].append(rssi)
            if sq is not None:
                self.signal_quality[mac].append(sq)
            if act is not None:
                self.activity[mac].append(act)
            if ch is not None:
                self.channels[mac].append(ch)
            if ft is not None:
                self.frame_types[mac].append(ft)

            # Not enough data yet
            if len(self.rssi[mac]) < MIN_PROFILE_SIZE:
                return None

            # Compute deviation
            return float(self._compute_deviation(mac, frame))

    # -----------------------------
    # Internal: deviation scoring
    # -----------------------------
    def _compute_deviation(self, mac, frame):
        """
        Compute how different this frame is from the device's baseline.
        Returns a score in [0, 1].
        """

        # Baselines
        rssi_mean = np.mean(self.rssi[mac])
        sq_mean = np.mean(self.signal_quality[mac]) if self.signal_quality[mac] else 0
        act_mean = np.mean(self.activity[mac]) if self.activity[mac] else 0

        # Current values
        rssi = frame.get("rssi") or 0
        sq = frame.get("signal_quality") or 0
        act = frame.get("activity_score") or 0

        # Deviations (normalized)
        rssi_dev = abs(rssi - rssi_mean) / 50.0
        sq_dev = abs(sq - sq_mean) / 50.0
        act_dev = abs(act - act_mean) / 50.0

        # Frame type deviation
        ft = frame.get("frame_type")
        ft_dev = 0
        if ft is not None:
            ft_dev = 0 if ft in self.frame_types[mac] else 1

        # Channel deviation
        ch = frame.get("channel")
        ch_dev = 0
        if ch is not None:
            # If channel rarely used, treat as anomaly
            ch_dev = 0 if ch in self.channels[mac] else 1

        # Combine
        score = (
            0.4 * rssi_dev +
            0.2 * sq_dev +
            0.2 * act_dev +
            0.1 * ft_dev +
            0.1 * ch_dev
        )

        # Clamp
        if score < 0:
            score = 0
        if score > 1:
            score = 1

        return score


# Singleton instance
engine = DeviceModel()
