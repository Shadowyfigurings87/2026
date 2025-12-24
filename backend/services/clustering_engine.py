# services/clustering_engine.py

import time
import threading
import numpy as np
from sklearn.cluster import MiniBatchKMeans

from utils.logging_config import log_event

CLUSTER_COUNT = 5
TRAIN_INTERVAL = 60
MAX_BUFFER_SIZE = 5000


class ClusteringEngine:
    def __init__(self):
        self.model = None
        self.buffer = []
        self.lock = threading.Lock()
        self.last_train_time = 0

        # Background trainer
        t = threading.Thread(target=self._trainer_loop, daemon=True)
        t.start()

        log_event("clustering_engine", "INFO", "engine_initialized", {})

    # -----------------------------
    # Public API
    # -----------------------------
    def assign_cluster(self, features: np.ndarray):
        """
        Assign a cluster label to a feature vector.
        If no model exists yet, return None.
        """
        if features is None:
            return None

        with self.lock:
            self.buffer.append(features)
            if len(self.buffer) > MAX_BUFFER_SIZE:
                self.buffer = self.buffer[-MAX_BUFFER_SIZE:]

        if self.model is None:
            return None

        try:
            cluster_id = int(self.model.predict([features])[0])
            return self._cluster_label(cluster_id)
        except Exception as e:
            log_event("clustering_engine", "ERROR", "cluster_failed", {"error": str(e)})
            return None

    # -----------------------------
    # Internal: trainer loop
    # -----------------------------
    def _trainer_loop(self):
        while True:
            time.sleep(5)

            now = time.time()
            if now - self.last_train_time < TRAIN_INTERVAL:
                continue

            with self.lock:
                if len(self.buffer) < CLUSTER_COUNT * 20:
                    continue

                data = np.vstack(self.buffer)

            try:
                log_event("clustering_engine", "INFO", "training_start", {
                    "samples": data.shape[0],
                    "features": data.shape[1],
                })

                model = MiniBatchKMeans(
                    n_clusters=CLUSTER_COUNT,
                    batch_size=256,
                    random_state=42
                )
                model.fit(data)

                with self.lock:
                    self.model = model
                    self.last_train_time = time.time()

                log_event("clustering_engine", "INFO", "training_complete", {
                    "samples": data.shape[0]
                })

            except Exception as e:
                log_event("clustering_engine", "ERROR", "training_failed", {"error": str(e)})

    # -----------------------------
    # Internal: human-readable labels
    # -----------------------------
    def _cluster_label(self, cid: int) -> str:
        """
        Map cluster IDs to human-readable anomaly types.
        These can be tuned later.
        """
        mapping = {
            0: "rssi_anomaly",
            1: "frame_type_anomaly",
            2: "channel_anomaly",
            3: "device_behavior_anomaly",
            4: "timing_anomaly",
        }
        return mapping.get(cid, f"cluster_{cid}")


# Singleton instance
engine = ClusteringEngine()
