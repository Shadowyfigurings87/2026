import socket, time, threading
from gui.arduino import get_queue, get_serial

HOST = "8.tcp.ngrok.io"
PORT = 10520

def run_forwarder():
    q = get_queue()       # consume Arduino lines from queue
    ser = get_serial()    # still need serial object to send commands back

    def connect_socket():
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((HOST, PORT))
        print(f"Connected to host via {HOST}:{PORT}")
        return s

    s = connect_socket()

    # Thread to listen for host commands and relay to Arduino
    def listen_for_commands(sock):
        while True:
            try:
                cmd = sock.recv(1024).decode().strip()
                if cmd:
                    ser.write((cmd + "\n").encode())
                    print(f"Host → Arduino: {cmd}")
            except Exception as e:
                print(f"Command error: {e}")
                break

    threading.Thread(target=listen_for_commands, args=(s,), daemon=True).start()

    # Main loop: forward Arduino telemetry from queue to host
    while True:
        try:
            line = q.get()   # blocks until a line is available
            s.sendall((line + "\n").encode())
            print(f"Arduino → Host: {line}")
        except (BrokenPipeError, ConnectionResetError):
            print("Connection lost, reconnecting...")
            time.sleep(2)
            s.close()
            s = connect_socket()
