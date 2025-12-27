import time
from ministries.alfa.packet_sniffer import PacketSniffer
from ministries.alfa.analyzer import PacketAnalyzer
from ministries.utils.jsonl import encode_jsonl


def main():
    print("[alfa] ministry starting", flush=True)

    analyzer = PacketAnalyzer()
    sniffer = PacketSniffer(interface="wlan1", bpf_filter=None)

    while True:
        try:
            # sniff_stream() is an infinite generator
            for pkt in sniffer.sniff_stream():
                try:
                    obj = analyzer.handle_packet(pkt)
                    if obj is None:
                        continue

                    # Add ministry + timestamp
                    obj["ministry"] = "alfa"
                    obj["ts"] = time.time()

                    # Output JSONL to stdout
                    print(encode_jsonl(obj), end="", flush=True)

                except Exception as e:
                    print(f"[alfa] packet error: {e}", flush=True)
                    time.sleep(0.05)

        except Exception as e:
            print(f"[alfa] sniffer error: {e}", flush=True)
            time.sleep(1)
            # Recreate sniffer in case interface resets
            sniffer = PacketSniffer(interface="wlan1", bpf_filter=None)


if __name__ == "__main__":
    main()
