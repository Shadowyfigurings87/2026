# /home/zachariah/2026/main.py

def main():
    print("Project root main.py starting…")

    from host.main import start_host
    from mapping.main import start_mapping

    # Start mapping ministry
    mapping_processes = start_mapping()

    # Start host ministry
    start_host()

if __name__ == "__main__":
    main()
