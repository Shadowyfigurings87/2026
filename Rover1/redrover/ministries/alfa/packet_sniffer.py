import os
from typing import Callable, Iterable, Optional

from scapy.all import sniff  # type: ignore
from scapy.packet import Packet  # type: ignore


class PacketSniffer:
    def __init__(
        self,
        interface: Optional[str] = None,
        bpf_filter: Optional[str] = None,
    ) -> None:
        """
        Generic packet sniffer.

        :param interface: monitor-mode interface name
        :param bpf_filter: optional BPF filter (e.g., 'wlan type mgt')
        """

        # Allow override via environment variable
        self.interface = interface or os.environ.get("ALFA_IFACE", "wlan1")
        self.bpf_filter = bpf_filter

    def sniff_stream(self) -> Iterable[Packet]:
        while True:
            pkts = sniff(
                iface=self.interface,
                filter=self.bpf_filter,
                store=True,
                count=1,
            )
            for pkt in pkts:
                yield pkt

    def run(
        self,
        packet_callback: Optional[Callable[[Packet], None]] = None,
        count: int = 0,
        timeout: Optional[int] = None,
    ) -> None:
        sniff(
            iface=self.interface,
            prn=packet_callback,
            filter=self.bpf_filter,
            store=False,
            count=count,
            timeout=timeout,
        )

