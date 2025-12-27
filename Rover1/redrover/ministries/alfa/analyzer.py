from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, Any

from scapy.layers.dot11 import Dot11, Dot11Beacon, Dot11ProbeReq  # type: ignore
from scapy.packet import Packet  # type: ignore


@dataclass
class FrameSummary:
    ts: datetime
    src: Optional[str]
    dst: Optional[str]
    bssid: Optional[str]
    frame_type: str
    ssid: Optional[str]
    rssi: Optional[int]


class PacketAnalyzer:
    """
    Analyzer that turns raw 802.11 packets into JSONL-ready summaries.

    Extend this to:
    - feed backend ingest
    - log anomalies
    - trigger rover behavior
    """

    def summarize(self, pkt: Packet) -> Optional[FrameSummary]:
        if not pkt.haslayer(Dot11):
            return None

        dot11 = pkt[Dot11]

        frame_type = f"{dot11.type}/{dot11.subtype}"
        src = dot11.addr2
        dst = dot11.addr1
        bssid = dot11.addr3
        ssid = None

        # Basic management frame parsing (beacon / probe request)
        if pkt.haslayer(Dot11Beacon) or pkt.haslayer(Dot11ProbeReq):
            info = getattr(pkt, "info", b"")
            if isinstance(info, bytes):
                ssid = info.decode(errors="ignore") or None
            else:
                ssid = str(info)

        # RSSI (signal strength) is driver-dependent; sometimes appears in RadioTap
        rssi = None
        if hasattr(pkt, "dBm_AntSignal"):
            try:
                rssi = int(pkt.dBm_AntSignal)
            except (TypeError, ValueError):
                rssi = None

        return FrameSummary(
            ts=datetime.utcnow(),
            src=src,
            dst=dst,
            bssid=bssid,
            frame_type=frame_type,
            ssid=ssid,
            rssi=rssi,
        )

    def to_dict(self, summary: FrameSummary) -> Dict[str, Any]:
        """
        Convert FrameSummary into a JSON-serializable dict suitable for JSONL.
        """
        return {
            "ts": summary.ts.isoformat(),
            "src": summary.src,
            "dst": summary.dst,
            "bssid": summary.bssid,
            "frame_type": summary.frame_type,
            "ssid": summary.ssid,
            "rssi": summary.rssi,
        }

    def handle_packet(self, pkt: Packet) -> Optional[Dict[str, Any]]:
        """
        Public entry point to connect to PacketSniffer.

        Returns a JSON-serializable dict, or None if packet is ignored.
        """
        summary = self.summarize(pkt)
        if summary is None:
            return None

        obj = self.to_dict(summary)

        # You can still log locally if you want:
        # print(
        #     f"[{obj['ts']}] type={obj['frame_type']} "
        #     f"src={obj['src']} dst={obj['dst']} bssid={obj['bssid']} "
        #     f"ssid={obj['ssid']!r} rssi={obj['rssi']}"
        # )

        return obj

