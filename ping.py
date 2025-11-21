# ping.py
import socket
import time

# List of nodes to probe (replace with actual IPs of your other systems)
NODES = [
    ("192.168.1.101", 5000),
    ("192.168.1.102", 5000),
    ("192.168.1.103", 5000),
]

def ping_node(host, port):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(3)  # timeout for unreachable nodes
            s.connect((host, port))
            s.sendall(b"ping")
            data = s.recv(1024).decode()
            return data.strip()
    except Exception as e:
        return f"error: {e}"

def heartbeat_cycle():
    while True:
        print("\n--- Heartbeat Sweep ---")
        for host, port in NODES:
            response = ping_node(host, port)
            print(f"Stardate log: {host}:{port} → {response}")
        time.sleep(10)  # wait 10 seconds before next sweep

if __name__ == "__main__":
    heartbeat_cycle()
