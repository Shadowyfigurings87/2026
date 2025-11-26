from gui.arduino import serial_queue
import socket, time

HOST = "0.tcp.ngrok.io"
PORT = 12958

def run_forwarder():
    def connect_socket():
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((HOST, PORT))
        print(f"Connected to host via {HOST}:{PORT}")
        return s

    s = connect_socket()

    while True:
        try:
            line = serial_queue.get()   # blocks until data available
            s.sendall((line + "\n").encode())
            print(f"Forwarded Arduino → Host: {line}")
        except (BrokenPipeError, ConnectionResetError):
            print("Connection lost, reconnecting...")
            time.sleep(2)
            s.close()
            s = connect_socket()
