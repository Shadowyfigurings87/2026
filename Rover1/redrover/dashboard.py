import subprocess
import threading
import time
import sys
import os
from transport.tcp_client import TcpClient

# ---------------------------------------------------------
# Virtual environment activation for subprocesses
# ---------------------------------------------------------
VENV_PATH = "/home/balthazaar87/2026/venv"

ENV = os.environ.copy()
ENV["VIRTUAL_ENV"] = VENV_PATH
ENV["PATH"] = f"{VENV_PATH}/bin:" + ENV["PATH"]
ENV.pop("PYTHONHOME", None)   # must be removed for venv to work
ENV["ALFA_IFACE"] = "wlan1"

# ---------------------------------------------------------
# Ministries to supervise
# ---------------------------------------------------------
PROCESSES = [
    {"name": "alfa",   "cmd": ["python", "-m", "ministries.alfa.main"]},
    {"name": "esp32",  "cmd": ["python", "-m", "ministries.esp32.esp32"]},
]

ROVER1_HOST = "192.168.1.50"
ROVER1_PORT = 9000


# ---------------------------------------------------------
# Start a ministry subprocess
# ---------------------------------------------------------
def start_process(cfg):
    name = cfg["name"]
    cmd = cfg["cmd"]

    # Replace "python" with the venv interpreter
    if cmd[0] == "python":
        cmd[0] = sys.executable

    print(f"[dashboard] starting {name}: {' '.join(cmd)}", flush=True)

    return subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,   # keep stderr separate so we see full tracebacks
        text=True,
        bufsize=1,
        env=ENV,
    )


# ---------------------------------------------------------
# Stream ministry stdout
# ---------------------------------------------------------
def stream_stdout(name, popen, tcp_client):
    for line in popen.stdout:
        line = line.rstrip()
        print(f"[{name}] {line}", flush=True)

        # TCP failures must NEVER stop ministries
        try:
            tcp_client.send(line)
        except Exception as e:
            print(f"[dashboard] TCP send error (ignored): {e}", flush=True)


# ---------------------------------------------------------
# Stream ministry stderr (tracebacks, warnings)
# ---------------------------------------------------------
def stream_stderr(name, popen):
    for line in popen.stderr:
        line = line.rstrip()
        print(f"[{name}][ERR] {line}", flush=True)


# ---------------------------------------------------------
# Supervise a ministry (restart on crash)
# ---------------------------------------------------------
def supervise_process(cfg, tcp_client):
    name = cfg["name"]

    while True:
        popen = start_process(cfg)

        # stdout thread
        t1 = threading.Thread(
            target=stream_stdout,
            args=(name, popen, tcp_client),
            daemon=True,
        )
        t1.start()

        # stderr thread
        t2 = threading.Thread(
            target=stream_stderr,
            args=(name, popen),
            daemon=True,
        )
        t2.start()

        # Wait for ministry to exit
        popen.wait()
        print(f"[dashboard] {name} exited with code {popen.returncode}, restarting...", flush=True)
        time.sleep(1)


# ---------------------------------------------------------
# Main dashboard loop
# ---------------------------------------------------------
def main():
    print("[dashboard] starting ministries...")

    # TCP client runs independently and reconnects forever
    tcp_client = TcpClient(ROVER1_HOST, ROVER1_PORT)

    threads = []
    for cfg in PROCESSES:
        t = threading.Thread(
            target=supervise_process,
            args=(cfg, tcp_client),
            daemon=True,
        )
        t.start()
        threads.append(t)

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("[dashboard] Ctrl+C received, terminating ministries...")
        print("[dashboard] shutdown complete.")


if __name__ == "__main__":
    main()
