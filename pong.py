import socket

HOST = "0.0.0.0"   # listen on all interfaces
PORT = 5000        # must match the port you expose with ngrok

def run_receiver():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((HOST, PORT))
    s.listen(1)
    print(f"Listening on {HOST}:{PORT}...")

    conn, addr = s.accept()
    print(f"Client connected from {addr}")

    try:
        while True:
            data = conn.recv(1024).decode().strip()
            if not data:
                break
            print(f"Arduino → Host: {data}")
            # Here you could also write to a file, database, or GUI
    except Exception as e:
        print(f"Error: {e}")
    finally:
        conn.close()
        s.close()

if __name__ == "__main__":
    run_receiver()
