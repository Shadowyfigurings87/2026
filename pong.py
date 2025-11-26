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

def toggle_led(index):
    state = led_states[index].get()
    cmd = f"LED:{index}:{'1' if state else '0'}\n".encode()
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
root.title("Host Motor & LED Control")

rpm_var = tk.StringVar(value="Avg RPM:0")
ttk.Label(root, textvariable=rpm_var, font=("Arial", 14)).pack(pady=10)

pwm_scale = tk.Scale(root, from_=0, to=255, orient=tk.HORIZONTAL,
                     label="PWM Control", command=lambda v: send_pwm(int(v)))
pwm_scale.pack(fill="x", padx=10, pady=10)

ttk.Label(root, text="LED Controls").pack(pady=(12,6))
led_states = []
for i in range(6):
    var = tk.BooleanVar()
    chk = tk.Checkbutton(root, text=f"LED {i}", variable=var,
                         command=lambda i=i: toggle_led(i))
    chk.pack(anchor="w", padx=10)
    led_states.append(var)

log_box = tk.Text(root, height=10, width=60)
log_box.pack(fill="both", expand=True, padx=10, pady=(6,10))

start_server()
update_rpm_display()
root.mainloop()
