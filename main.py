# main.py

def main():
    print("Project root main.py starting…")

    # Eventually you may choose between Rover1, Host, etc.
    from host.main import start_host
    start_host()

if __name__ == "__main__":
    main()
