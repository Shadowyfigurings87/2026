import socket
import threading
import time

HOST = "0.0.0.0"
PORT = 5002

class CommandServer:
    def __init__(self):
        self.client_socket = None
        self.lock = threading.Lock()

        t = threading.Thread(target=self._start_server, daemon=True)
        t.start()

    def _start_server(self):
        while True:
            try:
                print(f"[CommandServer] Listening on {HOST}:{PORT}")
                server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                server.bind((HOST, PORT))
                server.listen(1)

                client, addr = server.accept()
                print(f"[CommandServer] Pi connected from {addr}")

                with self.lock:
                    self.client_socket = client

                # Block until client disconnects
                while True:
                    data = client.recv(1)
                    if not data:
                        break

            except Exception as e:
                print("[CommandServer] Error:", e)

            finally:
                print("[CommandServer] Pi disconnected")
                with self.lock:
                    self.client_socket = None
                time.sleep(1)

    def send_line(self, line: str):
        with self.lock:
            if not self.client_socket:
                print("[CommandServer] No Pi connected, dropping:", line)
                return

            try:
                self.client_socket.sendall((line + "\n").encode())
            except Exception as e:
                print("[CommandServer] Send failed:", e)
                self.client_socket = None


# Global instance
command_server = CommandServer()
