import socket, time
from gui.arduino import get_serial

HOST = "0.tcp.ngrok.io"
PORT = 12958

def run_forwarder():
    ser = get_serial()

    def connect_socket():
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((HOST, PORT))
        print(f"Connected to host via {HOST}:{PORT}")
        return s

    s = connect_socket()

    while True:
        try:
            line = ser.readline().decode().strip()
            if line:
                s.sendall((line + "\n").encode())
                print(f"Forwarded Arduino → Host: {line}")
        except (BrokenPipeError, ConnectionResetError):
            print("Connection lost, reconnecting...")
            time.sleep(2)
            s.close()
            s = connect_socket()
