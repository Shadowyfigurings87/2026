import serial, socket, time

ARDUINO_PORT = "/dev/ttyACM0"   # adjust to your client’s Arduino port
BAUD = 9600
HOST = "0.tcp.ngrok.io"
PORT = 12958                    # ngrok port

def run_forwarder():
    ser = serial.Serial(ARDUINO_PORT, BAUD, timeout=1)

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
        except Exception as e:
            print(f"Unexpected error: {e}")
            time.sleep(2)
