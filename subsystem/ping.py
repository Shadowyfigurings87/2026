import socket
import time

HOST = "192.168.1.171"   # Host machine ep1s0
PORT = 5000              # Listening port on host
TIMEOUT = 300            # 5 minutes in seconds

def persistent_ping():
    start_time = time.time()
    while time.time() - start_time < TIMEOUT:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(5)  # timeout for each attempt
                print(f"Attempting connection to {HOST}:{PORT}...")
                s.connect((HOST, PORT))
                s.sendall(b"ping")
                data = s.recv(1024).decode()
                print(f"Stardate log: {HOST}:{PORT} → {data.strip()}")
                return  # exit once successful
        except Exception as e:
            print(f"Connection failed: {e}")
            time.sleep(5)  # wait before retrying
    print("Persistent attempts ended after 5 minutes.")

if __name__ == "__main__":
    persistent_ping()
