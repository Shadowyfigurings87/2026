from typing import Callable, Iterable, Optional

from scapy.all import sniff  # type: ignore
from scapy.packet import Packet  # type: ignore


class PacketSniffer:
    def __init__(
        self,
        interface: str = "wlan1",
        bpf_filter: Optional[str] = None,
    ) -> None:
        """
        Generic packet sniffer.

        :param interface: monitor-mode interface name
        :param bpf_filter: optional BPF filter (e.g., 'wlan type mgt')
        """
        self.interface = interface
        self.bpf_filter = bpf_filter

    def sniff_stream(self) -> Iterable[Packet]:
        """
        Yield packets one by one in an infinite stream.

        This is designed to be used by a generator that feeds send_jsonl_stream().
        """
        while True:
            pkts = sniff(
                iface=self.interface,
                filter=self.bpf_filter,
                store=True,
                count=1,  # capture one packet at a time
            )
            for pkt in pkts:
                yield pkt

    def run(
        self,
        packet_callback: Optional[Callable[[Packet], None]] = None,
        count: int = 0,
        timeout: Optional[int] = None,
    ) -> None:
        """
        Convenience method if you want to run in callback mode.

        :param packet_callback: function(pkt) called for each packet
        :param count: number of packets to capture (0 = infinite)
        :param timeout: timeout in seconds
        """
        sniff(
            iface=self.interface,
            prn=packet_callback,
            filter=self.bpf_filter,
            store=False,
            count=count,
            timeout=timeout,
        )

