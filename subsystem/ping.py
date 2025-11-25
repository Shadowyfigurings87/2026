import socket
import time

# Define your ngrok endpoint here
HOST = "0.tcp.ngrok.io"   # replace with ngrok host
PORT = 12345              # replace with ngrok port
TIMEOUT = 300  # 5 minutes

def persistent_ping():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(5)
        print(f"Connecting to {HOST}:{PORT}...")
        s.connect((HOST, PORT))
        start_time = time.time()
        while time.time() - start_time < TIMEOUT:
            try:
                s.sendall(b"ping")
                data = s.recv(1024).decode()
                print(f"Stardate log: {HOST}:{PORT} → {data.strip()}")
                time.sleep(5)
            except Exception as e:
                print(f"Connection error: {e}")
                break

if __name__ == "__main__":
    persistent_ping()
