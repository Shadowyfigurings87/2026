import tkinter as tk
from tkinter import ttk
import socket, threading, queue, statistics

HOST = "0.0.0.0"
PORT = 5000  # ngrok forwards here

rpm_queue = queue.Queue()
host_conn = None  # global socket connection

def start_server():
    def server_thread():
        global host_conn
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind((HOST, PORT))
            s.listen()
            print(f"Host listener on {HOST}:{PORT}")
            while True:
                conn, addr = s.accept()
                print(f"Connection from {addr}")
                host_conn = conn
                threading.Thread(target=handle_client, args=(conn,), daemon=True).start()
    threading.Thread(target=server_thread, daemon=True).start()

def handle_client(conn):
    with conn:
        while True:
            data = conn.recv(1024).decode().strip()
            if not data:
                break
            if data.startswith("RPM:"):
                try:
                    rpm_queue.put(float(data.split(":")[1]))
                except:
                    pass

def send_pwm(value):
    cmd = f"PWM:{value}\n".encode()
    if host_conn:
        host_conn.sendall(cmd)
        log(f"Sent {cmd.strip()}")

# --- Actuator control functions ---
def send_actuator_forward(speed):
    cmd = f"ACT:FWD:{speed}\n".encode()
    if host_conn:
        host_conn.sendall(cmd)
        log(f"Sent {cmd.strip()}")

def send_actuator_reverse(speed):
    cmd = f"ACT:REV:{speed}\n".encode()
    if host_conn:
        host_conn.sendall(cmd)
        log(f"Sent {cmd.strip()}")

def send_actuator_stop():
    cmd = "ACT:STOP\n".encode()
    if host_conn:
        host_conn.sendall(cmd)
        log(f"Sent {cmd.strip()}")

# --- Direction control functions (Optocoupler F/R) ---
def send_dir_forward():
    cmd = "DIR:FWD\n".encode()
    if host_conn:
        host_conn.sendall(cmd)
        log(f"Sent {cmd.strip()}")

def send_dir_reverse():
    cmd = "DIR:REV\n".encode()
    if host_conn:
        host_conn.sendall(cmd)
        log(f"Sent {cmd.strip()}")

def log(msg):
    log_box.insert(tk.END, msg + "\n")
    log_box.see(tk.END)

def update_rpm_display():
    values = []
    while not rpm_queue.empty():
        values.append(rpm_queue.get())
    if values:
        avg = statistics.mean(values)
        rpm_var.set(f"Avg RPM: {avg:.2f}")
        log(f"Received {len(values)} samples, avg={avg:.2f}")
    root.after(1000, update_rpm_display)

root = tk.Tk()
root.title("Host Motor & Actuator Control")

rpm_var = tk.StringVar(value="Avg RPM:0")
ttk.Label(root, textvariable=rpm_var, font=("Arial", 14)).pack(pady=10)

# --- Motor PWM ---
pwm_scale = tk.Scale(root, from_=0, to=255, orient=tk.HORIZONTAL,
                     label="PWM Control", command=lambda v: send_pwm(int(v)))
pwm_scale.pack(fill="x", padx=10, pady=10)

# --- Actuator Controls ---
ttk.Label(root, text="Actuator Control").pack(pady=(12,6))
act_speed_scale = tk.Scale(root, from_=0, to=255, orient=tk.HORIZONTAL,
                           label="Actuator Speed")
act_speed_scale.set(128)
act_speed_scale.pack(fill="x", padx=10)

btn_frame = ttk.Frame(root)
btn_frame.pack(pady=8)
ttk.Button(btn_frame, text="Forward", command=lambda: send_actuator_forward(act_speed_scale.get())).pack(side="left", padx=5)
ttk.Button(btn_frame, text="Reverse", command=lambda: send_actuator_reverse(act_speed_scale.get())).pack(side="left", padx=5)
ttk.Button(btn_frame, text="Stop", command=send_actuator_stop).pack(side="left", padx=5)

# --- Direction Controls (Optocoupler F/R) ---
ttk.Label(root, text="Direction Control (Optocoupler)").pack(pady=(12,6))
dir_frame = ttk.Frame(root)
dir_frame.pack(pady=8)
ttk.Button(dir_frame, text="Forward Dir", command=send_dir_forward).pack(side="left", padx=5)
ttk.Button(dir_frame, text="Reverse Dir", command=send_dir_reverse).pack(side="left", padx=5)

# --- Log Box ---
log_box = tk.Text(root, height=10, width=60)
log_box.pack(fill="both", expand=True, padx=10, pady=(6,10))

start_server()
update_rpm_display()
root.mainloop()
