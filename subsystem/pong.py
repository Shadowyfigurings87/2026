# pong.py
import socket

HOST = "0.0.0.0"   # Listen on all interfaces
PORT = 5000        # Must match the port your ping client uses

def start_pong_server():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((HOST, PORT))
        s.listen()
        print(f"Pong server listening on {HOST}:{PORT}")
        
        while True:
            conn, addr = s.accept()
            with conn:
                print(f"Connection from {addr}")
                data = conn.recv(1024).decode().strip().lower()
                if data == "ping":
                    conn.sendall(b"pong")
                else:
                    conn.sendall(b"unknown command")

if __name__ == "__main__":
    start_pong_server()
