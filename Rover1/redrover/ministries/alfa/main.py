import threading
import queue
import time
import signal
import sys

from .packet_sniffer import PacketSniffer
from .channel_hopper import ChannelHopper
from .analyzer import PacketAnalyzer
from .state_engine import RFStateEngine


def main():
    print("[alfa] ministry starting")

    # Shared queue for sniffer → analyzer
    packet_queue = queue.Queue()

    # Instantiate RF state engine (event-driven RF intelligence)
    state_engine = RFStateEngine(
        event_cooldown=30.0,   # seconds between updates per device
        rssi_delta=5           # minimum RSSI change to trigger update
    )

    # Instantiate ministries
    sniffer = PacketSniffer(
        interface="wlan1",
        packet_queue=packet_queue
    )

    analyzer = PacketAnalyzer(
        packet_queue=packet_queue,
        state_engine=state_engine   # <-- NEW: inject event engine
    )

    hopper = ChannelHopper(
        interface="wlan1mon",
        dwell_time=0.5
    )

    # Thread wrappers
    sniffer_thread = threading.Thread(target=sniffer.run, daemon=True)
    analyzer_thread = threading.Thread(target=analyzer.run, daemon=True)
    hopper_thread = threading.Thread(target=hopper.run, daemon=True)

    # Start ministries
    sniffer_thread.start()
    analyzer_thread.start()
    hopper_thread.start()

    # Graceful shutdown handler
    def shutdown(signum, frame):
        print("\n[alfa] shutdown ritual invoked")
        sniffer.stop()
        analyzer.stop()
        hopper.stop()
        time.sleep(0.5)
        sys.exit(0)

    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    # Keep main thread alive
    while True:
        time.sleep(1)


if __name__ == "__main__":
    main()
