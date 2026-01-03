import json
import time
from scapy.layers.dot11 import Dot11, Dot11Beacon, Dot11ProbeReq


class PacketAnalyzer:
    def __init__(self, packet_queue):
        """
        Analyzer that consumes packets from a queue and emits JSON events.
        """
        self.packet_queue = packet_queue
        self.running = True

    def stop(self):
        """Signal the analyzer to stop."""
        self.running = False

    def _parse_packet(self, pkt):
        if not pkt.haslayer(Dot11):
            return None

        dot11 = pkt[Dot11]

        src = dot11.addr2
        dst = dot11.addr1
        bssid = dot11.addr3
        frame_type = f"{dot11.type}/{dot11.subtype}"

        # RSSI if present
        rssi = getattr(pkt, "dBm_AntSignal", None)

        # SSID for beacon/probe frames
        ssid = None
        if pkt.haslayer(Dot11Beacon) or pkt.haslayer(Dot11ProbeReq):
            if hasattr(pkt, "info"):
                try:
                    ssid = pkt.info.decode(errors="ignore")
                except Exception:
                    ssid = None

        event = {
            "ts": time.time(),
            "src": src,
            "dst": dst,
            "bssid": bssid,
            "frame_type": frame_type,
            "ssid": ssid,
            "rssi": rssi,
            "ministry": "alfa",
            "kind": "wifi_frame",
        }

        return event

    def run(self):
        """Main loop — called by main.py inside its own thread."""
        while self.running:
            pkt = self.packet_queue.get()
            parsed = self._parse_packet(pkt)
            if parsed:
                print(json.dumps(parsed), flush=True)

