import socket

HOST = "0.0.0.0"   # Listen on all interfaces
PORT = 5000

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.bind((HOST, PORT))
    s.listen()
    print(f"Pong server listening on {HOST}:{PORT}")
    while True:
        conn, addr = s.accept()
        with conn:
            print(f"Connection from {addr}")
            data = conn.recv(1024).decode()
            if data.strip() == "ping":
                conn.sendall(b"pong")
            else:
                conn.sendall(b"unknown command")
