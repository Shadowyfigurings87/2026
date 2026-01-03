import subprocess
import threading
import time
from typing import Iterable, List, Optional


class ChannelHopper:
    def __init__(
        self,
        interface: str = "wlan1mon",
        channels: Optional[Iterable[int]] = None,
        dwell_time: float = 0.5,
        include_dfs: bool = False,
    ) -> None:
        """
        Channel hopper for a monitor-mode interface.

        :param interface: interface in monitor mode (e.g., wlan1mon)
        :param channels: sequence of channel numbers (e.g., [1, 6, 11])
        :param dwell_time: seconds to stay on each channel
        :param include_dfs: whether to include DFS 5GHz channels
        """
        if channels is not None:
            self.channels: List[int] = list(channels)
        else:
            # Default: DFS-safe 2.4 GHz channels
            base_channels = list(range(1, 12))
            if include_dfs:
                dfs_channels = [
                    52, 56, 60, 64,
                    100, 104, 108, 112, 116, 120, 124, 128,
                    132, 136, 140, 144
                ]
                base_channels += dfs_channels
            self.channels = base_channels

        self.interface = interface
        self.dwell_time = dwell_time
        self._stop_event = threading.Event()

    def stop(self) -> None:
        """Signal the hopper to stop."""
        self._stop_event.set()

    def _set_channel(self, channel: int) -> None:
        try:
            subprocess.run(
                ["iw", "dev", self.interface, "set", "channel", str(channel)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=False,
            )
        except Exception:
            # Hopper should never crash the ministry
            pass

    def run(self) -> None:
        """Main loop — called by main.py inside its own thread."""
        while not self._stop_event.is_set():
            for ch in self.channels:
                if self._stop_event.is_set():
                    break
                self._set_channel(ch)
                time.sleep(self.dwell_time)
