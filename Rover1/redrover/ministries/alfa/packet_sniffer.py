from scapy.all import sniff


class PacketSniffer:
    def __init__(self, interface, packet_queue):
        """
        Packet sniffer for a monitor-mode interface.

        :param interface: interface in monitor mode (e.g., wlan1mon)
        :param packet_queue: queue to push captured packets into
        """
        self.interface = interface
        self.packet_queue = packet_queue
        self.running = True

    def stop(self):
        """Signal the sniffer to stop."""
        self.running = False

    def _handle_packet(self, pkt):
        # Push raw Scapy packet into queue for analyzer
        self.packet_queue.put(pkt)

    def run(self):
        """Main loop — called by main.py inside its own thread."""
        while self.running:
            sniff(
                iface=self.interface,
                prn=self._handle_packet,
                store=False,
                monitor=True,
            )
