# server.py
import socket

HOST = "0.0.0.0"   # Listen on all interfaces
PORT = 5000        # Choose a port >1024

def start_server():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((HOST, PORT))
        s.listen()
        print(f"Server listening on {HOST}:{PORT}")
        
        while True:
            conn, addr = s.accept()
            with conn:
                print(f"Connected by {addr}")
                data = conn.recv(1024).decode()
                if data.strip().lower() == "ping":
                    conn.sendall(b"pong")
                else:
                    conn.sendall(b"unknown command")

if __name__ == "__main__":
    start_server()
