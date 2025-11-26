import threading
from ping import run_ping
from gui import arduino

def main():
    # Run ping in background
    t1 = threading.Thread(target=run_ping, daemon=True)
    t1.start()

    # Launch Arduino GUI (blocking)
    arduino.run_gui()

if __name__ == "__main__":
    main()
