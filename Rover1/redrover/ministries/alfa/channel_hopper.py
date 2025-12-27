import subprocess
import threading
import time
from typing import Iterable, List, Optional


class ChannelHopper:
    def __init__(
        self,
        interface: str = "wlan1",
        channels: Optional[Iterable[int]] = None,
        dwell_time: float = 0.5,
    ) -> None:
        """
        Channel hopper for a monitor-mode interface.

        :param interface: interface in monitor mode (e.g., wlan1)
        :param channels: sequence of channel numbers (e.g., [1, 6, 11])
        :param dwell_time: seconds to stay on each channel
        """
        self.interface = interface
        self.channels: List[int] = list(channels or [1, 6, 11])
        self.dwell_time = dwell_time
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None

    def _set_channel(self, channel: int) -> None:
        subprocess.run(
            ["sudo", "iw", "dev", self.interface, "set", "channel", str(channel)],
            check=False,
        )

    def _run(self) -> None:
        while not self._stop_event.is_set():
            for ch in self.channels:
                if self._stop_event.is_set():
                    break
                self._set_channel(ch)
                time.sleep(self.dwell_time)

    def start(self) -> None:
        """Start channel hopping in a background thread."""
        if self._thread and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        """Stop channel hopping."""
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=2.0)

