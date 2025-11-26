from gui.arduino import serial_queue
import socket, time

HOST = "2.tcp.ngrok.io"
PORT = 11733

def run_forwarder():
    ser = get_serial()

    def connect_socket():
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((HOST, PORT))
        print(f"Connected to host via {HOST}:{PORT}")
        return s

    s = connect_socket()

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

    while True:
        try:
            line = ser.readline().decode().strip()
            if line:
                s.sendall((line + "\n").encode())
                print(f"Arduino → Host: {line}")
        except (BrokenPipeError, ConnectionResetError):
            print("Connection lost, reconnecting...")
            time.sleep(2)
            s.close()
            s = connect_socket()
