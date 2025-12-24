import os
import time
import threading
import pickle

import numpy as np
from sklearn.ensemble import IsolationForest

from utils.logging_config import log_event

MODEL_PATH = "data/anomaly_model.pkl"

# How often to retrain (seconds)
TRAIN_INTERVAL = 60

# Minimum frames before we train the first model
MIN_TRAIN_SIZE = 500

# Max frames kept in buffer (rolling window)
MAX_BUFFER_SIZE = 5000


class AnomalyEngine:
    def __init__(self):
        self.model = None
        self.buffer = []     # list of feature vectors (np.array)
        self.lock = threading.Lock()
        self.last_train_time = 0

        self._load_model()

        # Background trainer thread
        t = threading.Thread(target=self._trainer_loop, daemon=True)
        t.start()

        log_event("anomaly_engine", "INFO", "engine_initialized", {})

    # -----------------------------
    # Public API
    # -----------------------------
    def score_frame(self, frame: dict):
        """
        Ingest a frame, update buffer, and return anomaly_score (float or None).

        - Extracts features
        - Adds to buffer
        - If model exists: returns anomaly score
        - If no model yet: returns None
        """
        features = self._extract_features(frame)
        if features is None:
            return None

        # Add to rolling buffer
        with self.lock:
            self.buffer.append(features)
            if len(self.buffer) > MAX_BUFFER_SIZE:
                self.buffer = self.buffer[-MAX_BUFFER_SIZE:]

        # If we have a model, score immediately
        if self.model is not None:
            try:
                # IsolationForest.decision_function: higher = more normal
                # We invert and normalize roughly into [0, 1]
                raw = -self.model.decision_function([features])[0]
                score = float(self._normalize_score(raw))
                return score
            except Exception as e:
                log_event("anomaly_engine", "ERROR", "score_failed", {"error": str(e)})
                return None

        # No model yet
        return None

    # -----------------------------
    # Internal: feature extraction
    # -----------------------------
    def _extract_features(self, f: dict):
        """
        Convert a frame dict into a numeric feature vector.

        This is intentionally robust: missing fields default to 0.
        """
        try:
            def enc(x):
                if x is None:
                    return 0
                return hash(str(x)) % 1000

            return np.array([
                f.get("rssi") or 0,
                f.get("rssi_normalized") or 0,
                f.get("signal_quality") or 0,
                f.get("rate") or 0,
                f.get("channel") or 0,

                enc(f.get("frame_type")),
                enc(f.get("subtype")),
                enc(f.get("direction")),

                enc(f.get("src_role")),
                enc(f.get("dst_role")),
                enc(f.get("bssid_role")),

                f.get("activity_score") or 0,
            ], dtype=float)
        except Exception as e:
            log_event("anomaly_engine", "ERROR", "feature_extraction_failed", {"error": str(e)})
            return None

    # -----------------------------
    # Internal: trainer loop
    # -----------------------------
    def _trainer_loop(self):
        """
        Background loop that periodically retrains the IsolationForest
        on the rolling buffer.
        """
        while True:
            time.sleep(5)  # check often; only train when needed

            now = time.time()
            if now - self.last_train_time < TRAIN_INTERVAL:
                continue

            with self.lock:
                if len(self.buffer) < MIN_TRAIN_SIZE:
                    continue

                data = np.vstack(self.buffer)  # shape: (N, D)

            try:
                log_event("anomaly_engine", "INFO", "training_start", {
                    "samples": data.shape[0],
                    "features": data.shape[1],
                })

                model = IsolationForest(
                    n_estimators=200,
                    contamination=0.01,
                    random_state=42,
                    warm_start=False,
                    n_jobs=-1,
                )
                model.fit(data)

                with self.lock:
                    self.model = model
                    self.last_train_time = time.time()

                self._save_model(model)

                log_event("anomaly_engine", "INFO", "training_complete", {
                    "samples": data.shape[0]
                })

            except Exception as e:
                log_event("anomaly_engine", "ERROR", "training_failed", {"error": str(e)})

    # -----------------------------
    # Internal: model persistence
    # -----------------------------
    def _load_model(self):
        if not os.path.exists(MODEL_PATH):
            return
        try:
            with open(MODEL_PATH, "rb") as f:
                self.model = pickle.load(f)
            log_event("anomaly_engine", "INFO", "model_loaded", {})
        except Exception as e:
            log_event("anomaly_engine", "ERROR", "model_load_failed", {"error": str(e)})
            self.model = None

    def _save_model(self, model):
        try:
            os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
            with open(MODEL_PATH, "wb") as f:
                pickle.dump(model, f)
            log_event("anomaly_engine", "INFO", "model_saved", {})
        except Exception as e:
            log_event("anomaly_engine", "ERROR", "model_save_failed", {"error": str(e)})

    # -----------------------------
    # Internal: score normalization
    # -----------------------------
    def _normalize_score(self, raw: float):
        """
        IsolationForest decision_function outputs values where:
        - higher = more normal
        - lower (negative) = more anomalous

        We invert and squash into roughly [0, 1] where:
        0 = normal, 1 = highly anomalous.
        """
        # This is a heuristic; can be tuned
        # Shift and scale based on rough expected range.
        # Clamp for safety.
        s = raw
        # raw often around [-0.5, 0.5]; adjust as needed
        s = (s + 0.5)  # shift
        s = 1.0 - s    # invert
        if s < 0:
            s = 0
        if s > 1:
            s = 1
        return s


# Singleton instance
engine = AnomalyEngine()
