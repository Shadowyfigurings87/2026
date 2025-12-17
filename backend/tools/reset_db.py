# tools/reset_db.py

import os
from utils.config import get_db_path
from tools.init_db import main as init_db


def main():
    db_path = get_db_path()

    if os.path.exists(db_path):
        print(f"Deleting existing DB: {db_path}")
        os.remove(db_path)

    print("Rebuilding database...")
    init_db()


if __name__ == "__main__":
    main()
