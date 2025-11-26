import socket

HOST = "0.0.0.0"
PORT = 5000  # must match the local port ngrok forwards to

def start_host_listener():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((HOST, PORT))
        s.listen()
        print(f"Host listener on {HOST}:{PORT}")
        while True:
            conn, addr = s.accept()
            print(f"Connection from {addr}")
            with conn:
                while True:
                    data = conn.recv(1024).decode().strip()
                    if not data:
                        break
                    print(f"Arduino → Host: {data}")

if __name__ == "__main__":
    start_host_listener()
