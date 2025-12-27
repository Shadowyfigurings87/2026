import subprocess
import threading
import time
import sys
from transport.tcp_client import TcpClient


# Ministries to supervise
PROCESSES = [
    {
        "name": "alfa",
        "cmd": ["python", "-m", "ministries.alfa.main"],
    },
    {
        "name": "camera",
        "cmd": ["python", "-m", "ministries.camera.cam"],
    },
    {
        "name": "esp32",
        "cmd": ["python", "-m", "ministries.esp32.esp32"],
    },
]


ROVER1_HOST = "192.168.1.50"   # <-- set this to Rover1's IP
ROVER1_PORT = 9000


def start_process(cfg):
    """Start a single ministry process and return the Popen object."""
    name = cfg["name"]
    cmd = cfg["cmd"]

    # Use same Python interpreter (venv-safe)
    if cmd[0] == "python":
        cmd[0] = sys.executable

    print(f"[dashboard] starting {name}: {' '.join(cmd)}", flush=True)

    return subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )


def stream_process_output(name, popen, tcp_client):
    """
    Read lines from a ministry's stdout and:
    - echo them to our own stdout (for logs)
    - forward JSONL lines to Rover1 via tcp_client
    """
    if popen.stdout is None:
        print(f"[dashboard] {name} has no stdout to read", flush=True)
        return

    for line in popen.stdout:
        if not line:
            continue

        # Keep raw line
        raw = line.rstrip("\n")

        # Log locally
        print(f"[{name}] {raw}", flush=True)

        # Forward to Rover1 (assumes line is JSONL)
        try:
            tcp_client.send(line)
        except Exception as e:
            print(f"[dashboard] error forwarding from {name}: {e}", flush=True)


def main():
    tcp_client = TcpClient(ROVER1_HOST, ROVER1_PORT)

    procs = {}

    # Initial start
    for cfg in PROCESSES:
        proc = start_process(cfg)
        procs[cfg["name"]] = {"cfg": cfg, "popen": proc}

        # Start a thread to stream output and forward it
        t = threading.Thread(
            target=stream_process_output,
            args=(cfg["name"], proc, tcp_client),
            daemon=True,
        )
        t.start()

    try:
        # Supervision loop
        while True:
            for name, entry in list(procs.items()):
                popen = entry["popen"]
                cfg = entry["cfg"]

                # If process exited, restart it
                if popen.poll() is not None:
                    print(f"[dashboard] {name} exited with code {popen.returncode}, restarting...", flush=True)
                    new_proc = start_process(cfg)
                    procs[name]["popen"] = new_proc

                    t = threading.Thread(
                        target=stream_process_output,
                        args=(name, new_proc, tcp_client),
                        daemon=True,
                    )
                    t.start()

            time.sleep(2)

    except KeyboardInterrupt:
        print("\n[dashboard] Ctrl+C received, terminating ministries...", flush=True)
        for name, entry in procs.items():
            popen = entry["popen"]
            if popen.poll() is None:
                print(f"[dashboard] terminating {name}...", flush=True)
                popen.terminate()
        print("[dashboard] shutdown complete.", flush=True)


if __name__ == "__main__":
    main()
