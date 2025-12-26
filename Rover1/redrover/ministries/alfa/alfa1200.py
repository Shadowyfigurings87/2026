import subprocess
import threading
import time
import queue
import re
from collections import defaultdict
from ministries.utils.jsonl import now_ts

WLAN_IFACE = "wlan1"

CHANNELS_24G = [1, 6, 11, 3, 9]
CHANNELS_5G = [36, 40, 44, 48, 149, 153, 157, 161]
CHANNEL_HOP_INTERVAL = 0.5


# -------------------------
# Channel Hopper Thread
# -------------------------
class ChannelHopper(threading.Thread):
    def __init__(self, iface, channels, interval=0.5):
        super().__init__(daemon=True)
        self.iface = iface
        self.channels = channels
        self.interval = interval
        self._stop = threading.Event()

    def stop(self):
        self._stop.set()

    def run(self):
        while not self._stop.is_set():
            for ch in self.channels:
                if self._stop.is_set():
                    break
                subprocess.run(
                    ["iw", "dev", self.iface, "set", "channel", str(ch)],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
                time.sleep(self.interval)


# -------------------------
# Packet Sniffer Thread
# -------------------------
class PacketSniffer(threading.Thread):
    def __init__(self, iface, out_queue):
        super().__init__(daemon=True)
        self.iface = iface
        self.out_queue = out_queue
        self._stop = threading.Event()
        self.proc = None

        self.r_bssid = re.compile(r"BSSID[: ]([0-9a-fA-F:]{17})")
        self.r_rssi = re.compile(r"(-\d{1,3})dBm")
        self.r_ssid = re.compile(r"SSID(?:

\[|\()(.+?)(?:\]

|\))")

    def stop(self):
        self._stop.set()
        if self.proc and self.proc.poll() is None:
            self.proc.terminate()

    def run(self):
        cmd = [
            "tcpdump", "-l", "-I",
            "-i", self.iface,
            "-e", "-s", "256",
            "type", "mgt"
        ]

        try:
            self.proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                text=True,
                bufsize=1
            )
        except FileNotFoundError:
            self.out_queue.put({"error": "tcpdump_not_found"})
            return

        for line in self.proc.stdout:
            if self._stop.is_set():
                break
            parsed = self.parse_line(line.strip())
            if parsed:
                self.out_queue.put(parsed)

    def parse_line(self, line):
        info = {"timestamp": time.time(), "raw": line}

        bssid = self._match(self.r_bssid, line)
        rssi = self._match(self.r_rssi, line)
        ssid = self._match(self.r_ssid, line)

        if bssid:
            info["bssid"] = bssid.lower()
        if rssi:
            info["rssi_dbm"] = int(rssi)
        if ssid:
            info["ssid"] = ssid.strip()

        if any(k in info for k in ("bssid", "ssid", "rssi_dbm")):
            return info
        return None

    @staticmethod
    def _match(pattern, text):
        m = pattern.search(text)
        return m.group(1) if m else None


# -------------------------
# Analyzer
# -------------------------
class AlfaAnalyzer:
    def __init__(self):
        self.aps = defaultdict(dict)

    def ingest(self, pkt):
        ts = pkt["timestamp"]
        bssid = pkt.get("bssid")
        ssid = pkt.get("ssid")
        rssi = pkt.get("rssi_dbm")

        if bssid:
            ap = self.aps[bssid]
            ap["bssid"] = bssid
            ap["last_seen"] = ts
            ap["frame_count"] = ap.get("frame_count", 0) + 1
            if ssid:
                ap["ssid"] = ssid
            if rssi is not None:
                ap["last_rssi_dbm"] = rssi

    def snapshot(self):
        now = time.time()

        # prune old APs
        self.aps = {
            b: ap for b, ap in self.aps.items()
            if now - ap.get("last_seen", 0) < 120
        }

        return {
            "timestamp": now,
            "aps_count": len(self.aps),
            "aps": list(self.aps.values())
        }


# -------------------------
# Monitor Mode Helper
# -------------------------
def ensure_monitor_mode(iface):
    subprocess.run(["ip", "link", "set", iface, "down"])
    subprocess.run(["iw", "dev", iface, "set", "type", "monitor"])
    subprocess.run(["ip", "link", "set", iface, "up"])


# -------------------------
# Main Generator
# -------------------------
def alfa_stream():
    ensure_monitor_mode(WLAN_IFACE)

    channels = CHANNELS_24G + CHANNELS_5G
    hopper = ChannelHopper(WLAN_IFACE, channels, CHANNEL_HOP_INTERVAL)
    pkt_queue = queue.Queue(maxsize=1000)
    sniffer = PacketSniffer(WLAN_IFACE, pkt_queue)
    analyzer = AlfaAnalyzer()

    hopper.start()
    sniffer.start()

    last_snapshot = time.time()
    snapshot_interval = 2.0

    while True:
        try:
            try:
                pkt = pkt_queue.get(timeout=0.2)
                analyzer.ingest(pkt)
            except queue.Empty:
                pass

            now = time.time()
            if now - last_snapshot >= snapshot_interval:
                last_snapshot = now
                snap = analyzer.snapshot()

                yield {
                    "kind": "telemetry",
                    "source": "alfa",
                    "rover": "RedRover",
                    "ts": now_ts(),
                    "data": snap
                }

        except Exception as e:
            yield {
                "kind": "telemetry",
                "source": "alfa",
                "rover": "RedRover",
                "ts": now_ts(),
                "error": str(e)
            }
            time.sleep(1)

