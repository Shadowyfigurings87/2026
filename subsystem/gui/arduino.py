import tkinter as tk
from tkinter import ttk
import serial
import threading
import tkinter.font as tkfont

# Adjust to your Arduino's port (Linux example: /dev/ttyACM0)
PORT = "/dev/ttyACM0"
BAUD = 9600

# Open serial connection
ser = serial.Serial("/dev/ttyACM0", BAUD, timeout=1)

# Function to send PWM command
def send_pwm():
    value = pwm_scale.get()
    cmd = f"PWM:{value}\n"
    ser.write(cmd.encode())
    log(f"Sent {cmd.strip()}")

# Function to toggle LED
def toggle_led(index):
    state = led_states[index].get()
    cmd = f"{index}:{'1' if state else '0'}\n"
    ser.write(cmd.encode())
    log(f"Sent {cmd.strip()}")

# Function to log messages in GUI
def log(msg):
    log_box.insert(tk.END, msg + "\n")
    log_box.see(tk.END)

# Background thread to read RPM from Arduino
def read_serial():
    while True:
        try:
            line = ser.readline().decode().strip()
            if line:
                rpm_var.set(line)  # update RPM label
                log(f"Received {line}")
        except Exception as e:
            log(f"Error: {e}")
            break

# Dark theme styling
def apply_dark_theme(root):
    root.configure(bg="#0f1419")

    default_font = tkfont.nametofont("TkDefaultFont")
    default_font.configure(size=11)
    root.option_add("*Font", default_font)

    style = ttk.Style(root)
    style.theme_use("clam")

    style.configure(".", background="#0f1419", foreground="#e6edf3", fieldbackground="#0b1117")

    style.configure("TButton", background="#2f81f7", foreground="#e6edf3", padding=6, relief="flat")
    style.map("TButton",
              background=[("active", "#1f6feb")],
              foreground=[("disabled", "#8b949e"), ("!disabled", "#e6edf3")])

    style.configure("TLabel", background="#0f1419", foreground="#e6edf3")
    style.configure("TCheckbutton", background="#0f1419", foreground="#e6edf3")

def style_text_widget(widget):
    widget.configure(
        bg="#0b1117",
        fg="#e6edf3",
        insertbackground="#e6edf3",
        highlightthickness=1,
        highlightbackground="#22272e",
        relief="flat"
    )

# GUI setup
root = tk.Tk()
root.title("Arduino Motor & LED Control")

apply_dark_theme(root)

# PWM control
ttk.Label(root, text="Motor PWM").pack(pady=(8,4))
pwm_scale = tk.Scale(root, from_=0, to=255, orient=tk.HORIZONTAL)
pwm_scale.configure(bg="#0f1419", fg="#e6edf3",
                    troughcolor="#22272e", highlightthickness=0)
pwm_scale.pack(fill="x", padx=10)
ttk.Button(root, text="Set PWM", command=send_pwm).pack(pady=8)

# LED controls
ttk.Label(root, text="LED Controls").pack(pady=(12,6))
led_states = []
for i in range(6):
    var = tk.BooleanVar()
    chk = tk.Checkbutton(root, text=f"LED {i}", variable=var,
                         command=lambda i=i: toggle_led(i))
    chk.configure(bg="#0f1419", fg="#e6edf3",
                  activebackground="#0f1419",
                  activeforeground="#e6edf3",
                  selectcolor="#0f1419")
    chk.pack(anchor="w", padx=10)
    led_states.append(var)

# RPM display
rpm_var = tk.StringVar(value="RPM:0")
ttk.Label(root, textvariable=rpm_var, font=("Arial", 14)).pack(pady=10)

# Log box
log_box = tk.Text(root, height=10, width=60)
log_box.pack(fill="both", expand=True, padx=10, pady=(6,10))
style_text_widget(log_box)

# Start background thread
threading.Thread(target=read_serial, daemon=True).start()

root.mainloop()
