import tkinter as tk
from tkinter import ttk
import serial, threading, queue
import tkinter.font as tkfont

PORT = "/dev/ttyACM1"   # adjust to your Arduino port
BAUD = 9600

# Open serial connection once
ser = serial.Serial(PORT, BAUD, timeout=1)

# Shared queue for serial lines
serial_queue = queue.Queue()

def get_serial():
    return ser

def get_queue():
    return serial_queue

def send_pwm():
    value = pwm_scale.get()
    cmd = f"PWM:{value}\n"
    ser.write(cmd.encode())
    log(f"Sent {cmd.strip()}")

# --- Actuator control functions ---
def send_actuator_forward():
    speed = act_speed_scale.get()
    cmd = f"ACT:FWD:{speed}\n"
    ser.write(cmd.encode())
    log(f"Sent {cmd.strip()}")

def send_actuator_reverse():
    speed = act_speed_scale.get()
    cmd = f"ACT:REV:{speed}\n"
    ser.write(cmd.encode())
    log(f"Sent {cmd.strip()}")

def send_actuator_stop():
    cmd = "ACT:STOP\n"
    ser.write(cmd.encode())
    log(f"Sent {cmd.strip()}")

# --- Direction control functions (Optocoupler F/R) ---
def send_dir_forward():
    cmd = "DIR:FWD\n"
    ser.write(cmd.encode())
    log(f"Sent {cmd.strip()}")

def send_dir_reverse():
    cmd = "DIR:REV\n"
    ser.write(cmd.encode())
    log(f"Sent {cmd.strip()}")

def log(msg):
    log_box.insert(tk.END, msg + "\n")
    log_box.see(tk.END)

def read_serial():
    while True:
        try:
            line = ser.readline().decode().strip()
            if line:
                serial_queue.put(line)
                rpm_var.set(line)
                log(f"Received {line}")
        except Exception as e:
            log(f"Error: {e}")
            break

def apply_dark_theme(root):
    root.configure(bg="#0f1419")
    default_font = tkfont.nametofont("TkDefaultFont")
    default_font.configure(size=11)
    root.option_add("*Font", default_font)
    style = ttk.Style(root)
    style.theme_use("clam")
    style.configure(".", background="#0f1419", foreground="#e6edf3", fieldbackground="#0b1117")
    style.configure("TButton", background="#2f81f7", foreground="#e6edf3", padding=6, relief="flat")
    style.map("TButton", background=[("active", "#1f6feb")])
    style.configure("TLabel", background="#0f1419", foreground="#e6edf3")

def style_text_widget(widget):
    widget.configure(bg="#0b1117", fg="#e6edf3", insertbackground="#e6edf3",
                     highlightthickness=1, highlightbackground="#22272e", relief="flat")

def run_gui():
    global pwm_scale, rpm_var, log_box, act_speed_scale
    root = tk.Tk()
    root.title("Arduino Motor & Actuator Control")
    apply_dark_theme(root)

    # --- Motor PWM ---
    ttk.Label(root, text="Motor PWM").pack(pady=(8,4))
    pwm_scale = tk.Scale(root, from_=0, to=255, orient=tk.HORIZONTAL,
                         bg="#0f1419", fg="#e6edf3", troughcolor="#22272e", highlightthickness=0)
    pwm_scale.pack(fill="x", padx=10)
    ttk.Button(root, text="Set PWM", command=send_pwm).pack(pady=8)

    # --- Actuator Controls ---
    ttk.Label(root, text="Actuator Control").pack(pady=(12,6))
    act_speed_scale = tk.Scale(root, from_=0, to=255, orient=tk.HORIZONTAL,
                               bg="#0f1419", fg="#e6edf3", troughcolor="#22272e", highlightthickness=0)
    act_speed_scale.set(128)  # default mid-speed
    act_speed_scale.pack(fill="x", padx=10)

    btn_frame = ttk.Frame(root)
    btn_frame.pack(pady=8)
    ttk.Button(btn_frame, text="Forward", command=send_actuator_forward).pack(side="left", padx=5)
    ttk.Button(btn_frame, text="Reverse", command=send_actuator_reverse).pack(side="left", padx=5)
    ttk.Button(btn_frame, text="Stop", command=send_actuator_stop).pack(side="left", padx=5)

    # --- Direction Controls (Optocoupler F/R) ---
    ttk.Label(root, text="Direction Control (Optocoupler)").pack(pady=(12,6))
    dir_frame = ttk.Frame(root)
    dir_frame.pack(pady=8)
    ttk.Button(dir_frame, text="Forward Dir", command=send_dir_forward).pack(side="left", padx=5)
    ttk.Button(dir_frame, text="Reverse Dir", command=send_dir_reverse).pack(side="left", padx=5)

    # --- RPM Display ---
    rpm_var = tk.StringVar(value="RPM:0")
    ttk.Label(root, textvariable=rpm_var, font=("Arial", 14)).pack(pady=10)

    # --- Log Box ---
    log_box = tk.Text(root, height=10, width=60)
    log_box.pack(fill="both", expand=True, padx=10, pady=(6,10))
    style_text_widget(log_box)

    threading.Thread(target=read_serial, daemon=True).start()
    root.mainloop()

# Run the GUI
if __name__ == "__main__":
    run_gui()
