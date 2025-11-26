import threading
from gui import arduino
from serial_forwarder import run_forwarder

def main():
    # Start serial forwarder in background
    t1 = threading.Thread(target=run_forwarder, daemon=True)
    t1.start()

    # Launch Arduino GUI (blocking)
    arduino.run_gui()

if __name__ == "__main__":
    main()
