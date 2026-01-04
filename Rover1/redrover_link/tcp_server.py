import socket
import threading
import queue
import logging
import traceback

# ---------------------------------------------------------
# Logging Setup
# ---------------------------------------------------------
logging.basicConfig(
    filename="tcp_server.log",
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

# Queue for raw JSONL lines from RedRover
redrover_queue = queue.Queue()


# ---------------------------------------------------------
# Handle a single client connection
# ---------------------------------------------------------
def _handle_client(conn, addr):
    thread_name = threading.current_thread().name
    logging.info(f"[{thread_name}] Handler started for {addr}")
    print(f"[RedRoverLink] Handler started for {addr}")

    try:
        with conn, conn.makefile("r") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue

                # Log + print incoming data
                logging.info(f"[{addr}] {line}")
                print(f"[RedRoverLink] {addr} → {line}")

                redrover_queue.put(line)

    except Exception as e:
        logging.error(f"Exception in handler for {addr}: {e}")
        logging.error(traceback.format_exc())
        print(f"[RedRoverLink] ERROR in handler for {addr}: {e}")

    finally:
        logging.info(f"Connection closed: {addr}")
        print(f"[RedRoverLink] Connection closed: {addr}")


# ---------------------------------------------------------
# Start the TCP server
# ---------------------------------------------------------
def start_redrover_server(host="0.0.0.0", port=9000):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((host, port))
    s.listen(5)

    logging.info(f"[RedRoverLink] Listening on {host}:{port}")
    print(f"[RedRoverLink] Listening on {host}:{port}")

    def accept_loop():
        while True:
            try:
                conn, addr = s.accept()
                logging.info(f"Connection from {addr}")
                print(f"[RedRoverLink] Connection from {addr}")

                t = threading.Thread(
                    target=_handle_client,
                    args=(conn, addr),
                    daemon=True,
                    name=f"ClientHandler-{addr[0]}:{addr[1]}"
                )
                t.start()

            except Exception as e:
                logging.error(f"Accept loop error: {e}")
                logging.error(traceback.format_exc())
                print(f"[RedRoverLink] ERROR in accept loop: {e}")

    threading.Thread(target=accept_loop, daemon=True, name="AcceptLoop").start()


# ---------------------------------------------------------
# Optional: Run directly
# ---------------------------------------------------------
if __name__ == "__main__":
    start_redrover_server()
    print("[RedRoverLink] Server running. Press Ctrl+C to exit.")

    # Keep main thread alive
    try:
        while True:
            pass
    except KeyboardInterrupt:
        print("\n[RedRoverLink] Shutdown requested.")
