import socket, time, threading, json
from modules.arduino import get_queue as get_arduino_queue, get_serial
from modules.cam import get_camera_queue
# from modules.scan import get_scan_queue   # future

HOST = "0.tcp.ngrok.io"
PORT = 17013

def jsonl_send(sock, obj):
    """Send a JSON object as JSONL."""
    line = json.dumps(obj) + "\n"
    sock.sendall(line.encode())

def run_forwarder():
    arduino_q = get_arduino_queue()
    camera_q  = get_camera_queue()
    # scan_q    = get_scan_queue()   # future
    ser = get_serial()

    def connect_socket():
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((HOST, PORT))
        print(f"Connected to host via {HOST}:{PORT}")
        return s

    s = connect_socket()

    # --- Host → Rover commands ---
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

    # --- Rover → Host telemetry ---
    while True:
        try:
            # Arduino telemetry
            if not arduino_q.empty():
                line = arduino_q.get()
                jsonl_send(s, {"type": "arduino", "line": line})

            # Camera frames
            if not camera_q.empty():
                frame = camera_q.get()  # raw numpy array
                # You will later encode this as JPEG + base64
                jsonl_send(s, {"type": "camera", "note": "raw_frame_received"})

            # RF scan (future)
            # if not scan_q.empty():
            #     event = scan_q.get()
            #     jsonl_send(s, event)

        except (BrokenPipeError, ConnectionResetError):
            print("Connection lost, reconnecting...")
            time.sleep(2)
            s.close()
            s = connect_socket()
