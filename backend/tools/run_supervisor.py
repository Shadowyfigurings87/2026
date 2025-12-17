# tools/run_supervisor.py

import time
import threading

from db_writer import start_writer_thread
import ml_ingest


def start_ingest_thread():
    """
    Launch ml_ingest.main() in its own thread.
    This keeps ingest running continuously while the supervisor stays alive.
    """
    t = threading.Thread(
        target=ml_ingest.main,
        name="ingest-thread",
        daemon=True
    )
    t.start()
    return t


def main():
    print("[+] Sovereign Supervisor Activated")
    print("[+] Initializing DB writer thread...")

    writer_thread = start_writer_thread()
    print("[+] DB writer thread online")

    print("[+] Starting ingest engine...")
    ingest_thread = start_ingest_thread()
    print("[+] Ingest engine online")

    print("[+] All systems running under supervisor control")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[!] Supervisor shutdown requested")
        print("[!] Daemon threads will terminate with process exit")
        print("[+] Goodbye")


if __name__ == "__main__":
    main()
